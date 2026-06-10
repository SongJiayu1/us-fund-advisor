#!/usr/bin/env node
/**
 * us-fund-advisor / generate-feed.js
 * 中央 Feed 生成器：抓取所有数据源并缓存到 ~/.us-fund-advisor/feed.json
 * 用法：node scripts/generate-feed.js
 */

const fs   = require("fs");
const path = require("path");
const os   = require("os");

const CONFIG_PATH  = path.join(__dirname, "../config.json");
const SOURCES_PATH = path.join(__dirname, "../sources.json");
const FEED_DIR     = path.join(os.homedir(), ".us-fund-advisor");
const FEED_PATH    = path.join(FEED_DIR, "feed.json");
const LOG_PATH     = path.join(__dirname, "../logs/generate-feed.log");

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  fs.mkdirSync(path.dirname(LOG_PATH), { recursive: true });
  fs.appendFileSync(LOG_PATH, line + "\n");
}

let config, sources;
try {
  config  = JSON.parse(fs.readFileSync(CONFIG_PATH,  "utf8"));
  sources = JSON.parse(fs.readFileSync(SOURCES_PATH, "utf8"));
} catch (e) {
  log(`❌ 读取配置失败: ${e.message}`);
  process.exit(1);
}

// ── 1. FRED 宏观数据 ──────────────────────────────────────────────────────────
async function fetchFred() {
  const results = {};
  const key = config.fred?.api_key;
  if (!key || key.startsWith("YOUR_")) {
    log("⚠️  FRED API key 未配置，跳过宏观数据");
    return results;
  }

  for (const series of sources.fred_series) {
    try {
      const url = `https://api.stlouisfed.org/fred/series/observations`
        + `?series_id=${series.id}&api_key=${key}&file_type=json`
        + `&sort_order=desc&limit=${sources.settings.fred_observation_count}`;
      const res  = await fetch(url);
      const data = await res.json();
      results[series.id] = {
        label:        series.label,
        sectors:      series.sectors,
        observations: (data.observations || []).map(o => ({
          date:  o.date,
          value: o.value === "." ? null : parseFloat(o.value)
        }))
      };
      log(`✅ FRED ${series.id}: ${results[series.id].observations[0]?.value}`);
    } catch (e) {
      log(`❌ FRED ${series.id} 失败: ${e.message}`);
    }
  }
  return results;
}

// ── 2. 市场行情 (Yahoo Finance v8 chart API) ──────────────────────────────────
async function fetchMarket() {
  const results = {};

  for (const t of sources.market_tickers) {
    try {
      const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(t.symbol)}?interval=1d&range=5d`;
      const res = await fetch(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
          "Accept": "application/json"
        }
      });
      const data = await res.json();
      const result = data.chart?.result?.[0];
      if (!result) {
        log(`⚠️  ${t.symbol}: 无数据`);
        continue;
      }

      const meta     = result.meta;
      const timestamps = result.timestamp;
      const closes   = result.indicators?.quote?.[0]?.close;
      const volumes  = result.indicators?.quote?.[0]?.volume;

      if (!closes || closes.length === 0) {
        log(`⚠️  ${t.symbol}: 无价格数据`);
        continue;
      }

      const lastIdx   = closes.length - 1;
      const prevIdx   = closes.length > 1 ? closes.length - 2 : lastIdx;
      const price     = closes[lastIdx];
      const prevClose = closes[prevIdx];
      const change    = price - prevClose;
      const changePct = prevClose ? (change / prevClose) * 100 : 0;

      results[t.symbol] = {
        label:         t.label,
        sectors:       t.sectors,
        price:         price,
        change:        change,
        changePct:     changePct,
        previousClose: prevClose,
        volume:        volumes?.[lastIdx],
        currency:      meta.currency,
        timestamp:     timestamps?.[lastIdx]
      };
      log(`✅ ${t.symbol}: ${price?.toFixed(2)} (${changePct?.toFixed(2)}%)`);
    } catch (e) {
      log(`❌ ${t.symbol} 失败: ${e.message}`);
    }
  }
  return results;
}

// ── 3. RSS 新闻 ────────────────────────────────────────────────────────────────
async function fetchRss() {
  const results = [];
  const maxAge  = sources.settings.max_age_hours * 60 * 60 * 1000;
  const cutoff  = Date.now() - maxAge;

  for (const feed of sources.rss_feeds) {
    try {
      const res  = await fetch(feed.url, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
          "Accept": "application/rss+xml,application/xml,text/xml,*/*"
        }
      });
      const text = await res.text();

      const items = [];
      const itemRegex = /<item>([\s\S]*?)<\/item>/g;
      let match;
      while ((match = itemRegex.exec(text)) !== null) {
        const block = match[1];
        const title = (/<title><!\[CDATA\[(.*?)\]\]><\/title>/.exec(block) ||
                       /<title>(.*?)<\/title>/.exec(block))?.[1]?.trim();
        const link  = (/<link>(.*?)<\/link>/.exec(block))?.[1]?.trim();
        const pubDate = (/<pubDate>(.*?)<\/pubDate>/.exec(block))?.[1]?.trim();
        const ts = pubDate ? new Date(pubDate).getTime() : Date.now();

        if (title && ts >= cutoff) {
          items.push({ title, link, pubDate, ts });
        }
        if (items.length >= sources.settings.rss_items_per_feed) break;
      }

      results.push({ source: feed.label, sectors: feed.sectors, items });
      log(`✅ RSS ${feed.label}: ${items.length} 条`);
    } catch (e) {
      log(`❌ RSS ${feed.url} 失败: ${e.message}`);
    }
  }
  return results;
}

// ── 4. X/Twitter（X API v2 Bearer Token）─────────────────────────────────────
async function fetchTwitter() {
  const results = [];
  const bearer = config.twitter?.bearer_token;
  if (!bearer || bearer.startsWith("YOUR_")) {
    log("⚠️  Twitter Bearer Token 未配置，跳过 X 数据");
    return results;
  }

  const headers = { Authorization: `Bearer ${bearer}` };

  for (const acct of sources.twitter_accounts) {
    try {
      // 1. 获取 user id
      const userRes = await fetch(
        `https://api.twitter.com/2/users/by/username/${acct.username}?user.fields=public_metrics,description`,
        { headers }
      );
      const userData = await userRes.json();
      if (!userData.data) {
        log(`⚠️  未找到用户 @${acct.username}`);
        continue;
      }
      const userId = userData.data.id;

      // 2. 获取最近推文
      const tweetRes = await fetch(
        `https://api.twitter.com/2/users/${userId}/tweets?tweet.fields=created_at,public_metrics&max_results=${sources.settings.twitter_tweets_per_account}`,
        { headers }
      );
      const tweetData = await tweetRes.json();

      const items = (tweetData.data || []).map(t => ({
        id:        t.id,
        text:      t.text,
        createdAt: t.created_at,
        likes:     t.public_metrics?.like_count,
        retweets:  t.public_metrics?.retweet_count
      }));

      results.push({
        username: acct.username,
        label:    acct.label,
        sectors:  acct.sectors,
        tweets:   items
      });
      log(`✅ @${acct.username}: ${items.length} 条推文`);
    } catch (e) {
      log(`❌ @${acct.username} 失败: ${e.message}`);
    }
  }
  return results;
}

// ── 主流程 ──────────────────────────────────────────────────────────────────
async function main() {
  log("=== 开始生成中央 Feed ===");
  fs.mkdirSync(FEED_DIR, { recursive: true });

  const [fred, market, rss, twitter] = await Promise.all([
    fetchFred(),
    fetchMarket(),
    fetchRss(),
    fetchTwitter()
  ]);

  const feed = {
    generated_at: new Date().toISOString(),
    fred,
    market,
    rss,
    twitter
  };

  fs.writeFileSync(FEED_PATH, JSON.stringify(feed, null, 2));
  log(`=== Feed 生成完成，已写入 ${FEED_PATH} ===`);
}

main().catch(e => {
  log(`❌ 致命错误: ${e.message}`);
  process.exit(1);
});
