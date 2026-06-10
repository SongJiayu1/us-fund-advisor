#!/bin/bash
# us-fund-advisor 每日定时任务脚本
# 用法: 由 launchd/cron 定时调用，或手动执行

set -e

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$SKILL_DIR/logs"

mkdir -p "$LOG_DIR"

# 按日期分割日志，避免单文件无限增长
LOG_FILE="$LOG_DIR/daily-cron-$(date +%Y%m%d).log"
exec >> "$LOG_FILE" 2>&1

# 清理 7 天前的旧日志
cd "$LOG_DIR"
find . -name "daily-cron-*.log" -mtime +7 -delete 2>/dev/null || true

# 截断过大的 launchd 日志（超过 1MB 时清空）
for f in launchd-out.log launchd-err.log; do
  if [ -f "$f" ] && [ "$(stat -f%z "$f" 2>/dev/null || echo 0)" -gt 1048576 ]; then
    : > "$f"
  fi
done

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 每日简报任务开始 ==="

cd "$SKILL_DIR"

# 1. 生成中央 Feed（FRED 宏观数据 + Yahoo Finance + RSS）
echo "[1/4] 生成中央 Feed..."
node scripts/generate-feed.js

# 2. AKShare 数据桥接（A股基金净值 + 美股历史行情）
echo "[2/4] AKShare 数据抓取..."
python3 scripts/fetch_akshare.py

# 3. 合并所有数据
echo "[3/4] 合并数据..."
node scripts/collect.js

# 4. Claude 分析并推送到飞书
#    如果你使用 Claude Code，可以 uncomment 下面这行：
# echo "[4/4] Claude 分析并推送..."
# claude --print --dangerously-skip-permissions "跑今日美股基金简报"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 每日简报任务结束 ==="
echo ""
