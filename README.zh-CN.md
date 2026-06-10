# US Fund Advisor

[English](README.md) | 中文

> 每日自动收集美股宏观数据，由 Claude AI 分析后生成基金操作建议，推送到飞书/ Lark。

## 功能

- **宏观数据自动采集**：对接 FRED（圣路易斯联储）API，每日拉取联邦基金利率、CPI、失业率、10 年期美债收益率、美元指数、VIX 恐慌指数、非农就业人数
- **AI 智能分析**：基于 Claude AI 的分析框架，生成纳斯达克、黄金、半导体、人工智能四个板块的操作建议（加仓 / 持有 / 减仓）
- **多渠道推送**：支持飞书 / Lark Webhook 消息卡片推送
- **可扩展数据源**：预留 Yahoo Finance、RSS 新闻、Twitter/X、AKShare 等接口，可按需启用
- **定时运行**：支持 macOS launchd 每日自动执行

## 效果预览

（此处可插入飞书推送截图）

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/SongJiayu1/us-fund-advisor.git
cd us-fund-advisor
```

### 2. 安装依赖

```bash
npm install

# 如需 AKShare 数据源（可选）
pip install akshare
```

### 3. 配置

```bash
cp config.template.json config.json
```

编辑 `config.json`，填写：

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| `feishu.webhook_url` | 飞书机器人推送地址 | 飞书群 → 设置 → 群机器人 → 自定义机器人 |
| `fred.api_key` | FRED 宏观数据 API Key | [免费申请](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `twitter.bearer_token` | X API v2 Bearer Token | [X Developer Portal](https://developer.twitter.com/)（可选） |

### 4. 测试运行

**手动执行完整流程：**

```bash
# 1. 生成中央 Feed（拉取所有数据源）
node scripts/generate-feed.js

# 2. 合并数据（生成 /tmp/us-fund-data.json）
node scripts/collect.js

# 3. 让 Claude 分析数据并生成结果（写入 /tmp/us-fund-result.json）
#    此步骤需在 Claude Code 中执行，或使用你自己的 AI 分析逻辑

# 4. 推送到飞书（dry-run 模式预览，不实际发送）
node scripts/deliver.js --dry-run

# 实际推送
node scripts/deliver.js --input /tmp/us-fund-result.json
```

**配合 Claude Code 使用：**

在 Claude Code 中直接说：

> "跑今日美股基金简报"

Claude 会自动执行：收集数据 → AI 分析 → 推送飞书。

### 5. 设置定时任务（可选）

```bash
# macOS launchd
# 复制并编辑 plist 模板，填入你的项目路径
# 然后加载：
launchctl load ~/Library/LaunchAgents/com.usfundadvisor.daily.plist
```

或使用 cron：

```bash
# 每天北京时间 6:00 执行
0 6 * * * /path/to/us-fund-advisor/scripts/run-daily.sh
```

## 数据源说明

| 数据源 | 状态 | 说明 |
|--------|------|------|
| **FRED 宏观数据** | 稳定可用 | 美联储官方数据，含利率、CPI、就业、VIX 等 7 个核心指标 |
| **Yahoo Finance** | 需适配 | 行情接口，目前存在反爬限制，建议寻找替代方案 |
| **RSS 新闻** | 部分可用 | 依赖源站点稳定性，可自定义替换 |
| **Twitter/X** | 需配置 | 需申请 X API v2 Bearer Token |
| **AKShare** | 可选 | A股基金净值、美股历史行情，需 Python 环境 |

## 目录结构

```
us-fund-advisor/
├── README.md                 # English README
├── README.zh-CN.md           # 本文件（中文）
├── LICENSE                   # MIT 协议
├── package.json              # Node.js 依赖
├── config.template.json      # 配置模板（复制为 config.json 后填写）
├── sources.json              # 数据源配置（X 账号、RSS、API 等）
├── funds.json                # 目标基金列表（可自定义）
├── prompts/
│   └── daily-briefing.md     # Claude AI 分析 Prompt 模板
└── scripts/
    ├── generate-feed.js      # 中央 Feed 生成器（拉取所有数据源）
    ├── collect.js            # 数据合并与预处理
    ├── deliver.js            # 飞书消息卡片推送
    ├── fetch_akshare.py      # AKShare 数据桥接（Python，可选）
    └── run-daily.sh          # 每日定时任务脚本
```

## 自定义

### 更换关注的板块或基金

编辑 `funds.json`，修改 `primary: true` 的基金为你实际持有的。

### 增减数据源

编辑 `sources.json`，可增删：
- `fred_series`：宏观指标
- `market_tickers`：行情标的
- `rss_feeds`：新闻源
- `twitter_accounts`：X 账号

### 调整 AI 分析风格

编辑 `prompts/daily-briefing.md`，修改分析框架、输出格式、语言风格。

## 技术栈

- **Node.js 18+**：数据收集、飞书推送
- **Claude AI**：市场分析与策略生成
- **FRED API**：宏观经济数据
- **飞书 / Lark Webhook**：消息推送
- **Python 3 + AKShare**（可选）：A股基金净值

## 免责声明

本工具由 AI 基于公开信息生成分析，仅供参考，**不构成投资建议**。投资有风险，操作需谨慎。

## License

MIT
