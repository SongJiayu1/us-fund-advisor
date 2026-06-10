#!/usr/bin/env node
/**
 * us-fund-advisor / collect.js
 * 读取中央 Feed（由 generate-feed.js 生成），输出到 /tmp/us-fund-data.json
 */

const fs   = require("fs");
const path = require("path");
const os   = require("os");

const CONFIG_PATH   = path.join(__dirname, "../config.json");
const FEED_PATH     = path.join(os.homedir(), ".us-fund-advisor", "feed.json");
const AKSHARE_PATH  = "/tmp/us-fund-akshare.json";
const OUTPUT_PATH   = "/tmp/us-fund-data.json";
const LOG_PATH      = path.join(__dirname, "../logs/collect.log");

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  fs.mkdirSync(path.dirname(LOG_PATH), { recursive: true });
  fs.appendFileSync(LOG_PATH, line + "\n");
}

async function main() {
  log("=== 开始收集数据 ===");

  if (!fs.existsSync(FEED_PATH)) {
    log(`❌ 中央 Feed 不存在: ${FEED_PATH}`);
    log("请先运行: node scripts/generate-feed.js");
    process.exit(1);
  }

  const feed = JSON.parse(fs.readFileSync(FEED_PATH, "utf8"));
  log(`📄 读取中央 Feed，生成时间: ${feed.generated_at}`);

  let akshare = null;
  if (fs.existsSync(AKSHARE_PATH)) {
    try {
      akshare = JSON.parse(fs.readFileSync(AKSHARE_PATH, "utf8"));
      log(`📄 读取 AKShare 数据，生成时间: ${akshare.generated_at}`);
    } catch (e) {
      log(`⚠️  读取 AKShare 数据失败: ${e.message}`);
    }
  }

  const output = {
    collected_at: new Date().toISOString(),
    fred:         feed.fred         || {},
    market:       feed.market       || {},
    rss:          feed.rss          || [],
    twitter:      feed.twitter      || [],
    akshare:      akshare           || null
  };

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(output, null, 2));
  log(`=== 收集完成，已写入 ${OUTPUT_PATH} ===`);

  // 同时保存带日期的备份
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
  if (config.output?.save_raw_data) {
    const dir  = path.join(__dirname, "../logs/raw");
    fs.mkdirSync(dir, { recursive: true });
    const date = new Date().toISOString().slice(0, 10);
    fs.writeFileSync(path.join(dir, `${date}.json`), JSON.stringify(output, null, 2));
    log(`💾 已保存备份: logs/raw/${date}.json`);
  }
}

main().catch(e => {
  log(`❌ 致命错误: ${e.message}`);
  process.exit(1);
});
