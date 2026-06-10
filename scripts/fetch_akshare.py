#!/usr/bin/env python3
"""
us-fund-advisor / fetch_akshare.py
AKShare 数据桥接脚本：抓取 A股基金/ETF 和美股数据，输出 JSON
用法: python3 scripts/fetch_akshare.py
输出: /tmp/us-fund-akshare.json
"""

import json
import sys
import time
import traceback
from datetime import datetime, timedelta

OUTPUT_PATH = "/tmp/us-fund-akshare.json"


def fetch_us_stock():
    """美股数据"""
    results = {}
    try:
        import akshare as ak

        # 1. 美股实时行情
        try:
            us_spot = ak.stock_us_spot_em()
            # 关注几个关键标的
            tickers = {
                "NDX": "NDX",      # 纳斯达克100
                "QQQ": "QQQ",      # 纳斯达克100 ETF
                "NVDA": "NVDA",    # 英伟达
                "AAPL": "AAPL",    # 苹果
                "MSFT": "MSFT",    # 微软
                "AMD": "AMD",      # AMD
                "TSM": "TSM",      # 台积电
                "SOXX": "SOXX",    # 半导体ETF
                "GLD": "GLD",      # 黄金ETF
            }
            stocks = []
            for _, row in us_spot.iterrows():
                symbol = str(row.get("代码", "")).strip()
                if symbol in tickers:
                    stocks.append({
                        "symbol": symbol,
                        "name": str(row.get("名称", "")),
                        "price": float(row.get("最新价", 0) or 0),
                        "change": float(row.get("涨跌额", 0) or 0),
                        "change_pct": float(row.get("涨跌幅", 0) or 0),
                        "volume": int(row.get("成交量", 0) or 0),
                        "market_cap": str(row.get("总市值", "")),
                        "pe_ttm": float(row.get("市盈率-动态", 0) or 0) if row.get("市盈率-动态") else None,
                        "source": "AKShare / stock_us_spot_em"
                    })
            if stocks:
                results["spot"] = stocks
                print(f"[OK] 美股实时行情: {len(stocks)} 只")
            else:
                print("[WARN] 美股实时行情: 未匹配到目标标的")
        except Exception as e:
            print(f"[ERR] 美股实时行情: {e}")

        # 2. 美股历史行情（QQQ）
        try:
            hist = ak.stock_us_daily(symbol="QQQ", adjust="qfq")
            if not hist.empty:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else latest
                results["qqq_hist"] = {
                    "latest_close": float(latest.get("close", 0)),
                    "latest_date": str(latest.get("date", "")),
                    "prev_close": float(prev.get("close", 0)),
                    "change_pct": round((float(latest.get("close", 0)) - float(prev.get("close", 0))) / float(prev.get("close", 0)) * 100, 2) if float(prev.get("close", 0)) else 0,
                    "volume": int(latest.get("volume", 0) or 0),
                    "source": "AKShare / stock_us_daily"
                }
                print(f"[OK] QQQ 历史行情: 最新 {results['qqq_hist']['latest_close']} ({results['qqq_hist']['change_pct']}%)")
        except Exception as e:
            print(f"[ERR] QQQ 历史行情: {e}")

        # 3. 英伟达历史行情
        try:
            hist = ak.stock_us_daily(symbol="NVDA", adjust="qfq")
            if not hist.empty:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else latest
                results["nvda_hist"] = {
                    "latest_close": float(latest.get("close", 0)),
                    "latest_date": str(latest.get("date", "")),
                    "prev_close": float(prev.get("close", 0)),
                    "change_pct": round((float(latest.get("close", 0)) - float(prev.get("close", 0))) / float(prev.get("close", 0)) * 100, 2) if float(prev.get("close", 0)) else 0,
                    "volume": int(latest.get("volume", 0) or 0),
                    "source": "AKShare / stock_us_daily"
                }
                print(f"[OK] NVDA 历史行情: 最新 {results['nvda_hist']['latest_close']} ({results['nvda_hist']['change_pct']}%)")
        except Exception as e:
            print(f"[ERR] NVDA 历史行情: {e}")

        # 4. 美股大盘指数
        try:
            indices = {
                ".IXIC": "纳斯达克综合指数",
                ".DJI": "道琼斯工业指数",
                ".INX": "标普500指数",
                ".NDX": "纳斯达克100指数",
            }
            index_data = {}
            for symbol, name in indices.items():
                try:
                    hist = ak.index_us_stock_sina(symbol=symbol)
                    if not hist.empty:
                        latest = hist.iloc[-1]
                        prev = hist.iloc[-2] if len(hist) > 1 else latest
                        index_data[symbol] = {
                            "name": name,
                            "latest_close": float(latest.get("close", 0)),
                            "latest_date": str(latest.get("date", "")),
                            "prev_close": float(prev.get("close", 0)),
                            "change_pct": round((float(latest.get("close", 0)) - float(prev.get("close", 0))) / float(prev.get("close", 0)) * 100, 2) if float(prev.get("close", 0)) else 0,
                            "volume": int(latest.get("volume", 0) or 0),
                            "source": "AKShare / index_us_stock_sina"
                        }
                        print(f"[OK] {name}({symbol}): 最新 {index_data[symbol]['latest_close']} ({index_data[symbol]['change_pct']}%)")
                except Exception as e:
                    print(f"[ERR] {name}({symbol}): {e}")
            if index_data:
                results["us_indices"] = index_data
        except Exception as e:
            print(f"[ERR] 美股大盘指数: {e}")

    except ImportError:
        print("[ERR] AKShare 未安装，请先运行: pip install akshare")
    except Exception as e:
        print(f"[ERR] 美股数据整体失败: {e}")
        traceback.print_exc()

    return results


def fetch_a_fund():
    """A股基金/ETF 数据（半导体 + AI）"""
    results = {}
    try:
        import akshare as ak

        # 1. 开放式基金实时净值
        try:
            fund_daily = ak.fund_open_fund_daily_em()
            # 动态列名：如 "2026-05-15-单位净值"
            nav_col = next((c for c in fund_daily.columns if c.endswith("-单位净值")), None)
            acc_nav_col = next((c for c in fund_daily.columns if c.endswith("-累计净值")), None)
            nav_date = "-".join(nav_col.split("-")[:3]) if nav_col else ""

            # 目标基金代码
            target_funds = {
                "014473": "广发中证半导体ETF联接A",
                "003986": "国联安中证全指半导体",
                "007419": "易方达中证人工智能A",
                "012994": "华夏中证人工智能ETF联接A",
                "008934": "华夏纳斯达克100ETF联接A",
                "270042": "广发纳斯达克100联接A",
                "000216": "华安黄金ETF联接A",
                "000307": "易方达黄金ETF联接A",
            }
            funds = []
            for _, row in fund_daily.iterrows():
                code = str(row.get("基金代码", "")).strip()
                if code in target_funds:
                    funds.append({
                        "code": code,
                        "name": target_funds.get(code, str(row.get("基金简称", ""))),
                        "nav": float(row.get(nav_col, 0) or 0) if nav_col else 0,
                        "nav_date": nav_date,
                        "daily_change_pct": float(row.get("日增长率", 0) or 0),
                        "accumulated_nav": float(row.get(acc_nav_col, 0) or 0) if acc_nav_col else 0,
                        "source": "AKShare / fund_open_fund_daily_em"
                    })
            if funds:
                results["open_fund"] = funds
                print(f"[OK] 开放式基金净值: {len(funds)} 只")
            else:
                print("[WARN] 开放式基金净值: 未匹配到目标基金")
        except Exception as e:
            print(f"[ERR] 开放式基金净值: {e}")

        # 2. ETF 历史行情 - 半导体 ETF (512480)
        try:
            end = datetime.now()
            start = end - timedelta(days=30)
            etf_semi = ak.fund_etf_hist_em(
                symbol="512480",
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq"
            )
            if not etf_semi.empty:
                latest = etf_semi.iloc[-1]
                prev = etf_semi.iloc[-2] if len(etf_semi) > 1 else latest
                results["semi_etf"] = {
                    "symbol": "512480",
                    "name": "国泰CES半导体芯片ETF",
                    "latest_close": float(latest.get("收盘", 0)),
                    "latest_date": str(latest.get("日期", "")),
                    "change_pct": round(float(latest.get("涨跌幅", 0) or 0), 2),
                    "volume": int(latest.get("成交量", 0) or 0),
                    "source": "AKShare / fund_etf_hist_em"
                }
                print(f"[OK] 半导体ETF(512480): 最新 {results['semi_etf']['latest_close']} ({results['semi_etf']['change_pct']}%)")
        except Exception as e:
            print(f"[ERR] 半导体ETF: {e}")

        time.sleep(5)

        # 3. ETF 历史行情 - AI ETF (159819)
        try:
            end = datetime.now()
            start = end - timedelta(days=30)
            etf_ai = ak.fund_etf_hist_em(
                symbol="159819",
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq"
            )
            if not etf_ai.empty:
                latest = etf_ai.iloc[-1]
                results["ai_etf"] = {
                    "symbol": "159819",
                    "name": "易方达中证人工智能ETF",
                    "latest_close": float(latest.get("收盘", 0)),
                    "latest_date": str(latest.get("日期", "")),
                    "change_pct": round(float(latest.get("涨跌幅", 0) or 0), 2),
                    "volume": int(latest.get("成交量", 0) or 0),
                    "source": "AKShare / fund_etf_hist_em"
                }
                print(f"[OK] AI ETF(159819): 最新 {results['ai_etf']['latest_close']} ({results['ai_etf']['change_pct']}%)")
        except Exception as e:
            print(f"[ERR] AI ETF: {e}")

        time.sleep(5)

        # 4. 纳斯达克 ETF (513100)
        try:
            end = datetime.now()
            start = end - timedelta(days=30)
            etf_nasdaq = ak.fund_etf_hist_em(
                symbol="513100",
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq"
            )
            if not etf_nasdaq.empty:
                latest = etf_nasdaq.iloc[-1]
                results["nasdaq_etf"] = {
                    "symbol": "513100",
                    "name": "国泰纳斯达克100ETF",
                    "latest_close": float(latest.get("收盘", 0)),
                    "latest_date": str(latest.get("日期", "")),
                    "change_pct": round(float(latest.get("涨跌幅", 0) or 0), 2),
                    "volume": int(latest.get("成交量", 0) or 0),
                    "source": "AKShare / fund_etf_hist_em"
                }
                print(f"[OK] 纳斯达克ETF(513100): 最新 {results['nasdaq_etf']['latest_close']} ({results['nasdaq_etf']['change_pct']}%)")
        except Exception as e:
            print(f"[ERR] 纳斯达克ETF: {e}")

        time.sleep(5)

        # 5. 黄金 ETF (518880)
        try:
            end = datetime.now()
            start = end - timedelta(days=30)
            etf_gold = ak.fund_etf_hist_em(
                symbol="518880",
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq"
            )
            if not etf_gold.empty:
                latest = etf_gold.iloc[-1]
                results["gold_etf"] = {
                    "symbol": "518880",
                    "name": "华安黄金ETF",
                    "latest_close": float(latest.get("收盘", 0)),
                    "latest_date": str(latest.get("日期", "")),
                    "change_pct": round(float(latest.get("涨跌幅", 0) or 0), 2),
                    "volume": int(latest.get("成交量", 0) or 0),
                    "source": "AKShare / fund_etf_hist_em"
                }
                print(f"[OK] 黄金ETF(518880): 最新 {results['gold_etf']['latest_close']} ({results['gold_etf']['change_pct']}%)")
        except Exception as e:
            print(f"[ERR] 黄金ETF: {e}")

    except ImportError:
        print("[ERR] AKShare 未安装，请先运行: pip install akshare")
    except Exception as e:
        print(f"[ERR] A股基金数据整体失败: {e}")
        traceback.print_exc()

    return results


def main():
    print("=== AKShare 数据抓取开始 ===")
    us_data = fetch_us_stock()
    cn_data = fetch_a_fund()

    output = {
        "generated_at": datetime.now().isoformat(),
        "us": us_data,
        "cn": cn_data
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"=== 完成，已写入 {OUTPUT_PATH} ===")


if __name__ == "__main__":
    main()
