# US Fund Advisor

English | [中文](README.md)

> Daily automated US stock macro data collection, AI-powered fund analysis, and Feishu/Lark push notifications.

## Features

- **Automated Macro Data Collection**: Integrates with the FRED (St. Louis Fed) API to pull daily Federal Funds Rate, CPI, Unemployment Rate, 10-Year Treasury Yield, US Dollar Index, VIX, and Non-Farm Payrolls.
- **AI-Powered Analysis**: Uses Claude AI to analyze macro trends and generate actionable fund recommendations (Buy / Hold / Reduce) for the Nasdaq, Gold, Semiconductors, and AI sectors.
- **Multi-Channel Delivery**: Supports Feishu / Lark Webhook message cards.
- **Extensible Data Sources**: Built-in support for Yahoo Finance, RSS news, Twitter/X, and AKShare, ready to enable as needed.
- **Scheduled Execution**: Supports daily automated runs via macOS launchd or cron.

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/SongJiayu1/us-fund-advisor.git
cd us-fund-advisor
```

### 2. Install dependencies

```bash
npm install

# Optional: AKShare data source (requires Python)
pip install akshare
```

### 3. Configure

```bash
cp config.template.json config.json
```

Edit `config.json` and fill in the following:

| Config Key | Description | How to Obtain |
|------------|-------------|---------------|
| `feishu.webhook_url` | Feishu bot push URL | Feishu Group → Settings → Group Bot → Custom Bot |
| `fred.api_key` | FRED macro data API key | [Apply for free](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `twitter.bearer_token` | X API v2 Bearer Token | [X Developer Portal](https://developer.twitter.com/) (optional) |

### 4. Run

**Execute the full pipeline manually:**

```bash
# 1. Generate central feed (pull all data sources)
node scripts/generate-feed.js

# 2. Merge and preprocess data (outputs to /tmp/us-fund-data.json)
node scripts/collect.js

# 3. Let Claude analyze the data and generate results (writes to /tmp/us-fund-result.json)
#    This step should be run inside Claude Code, or use your own AI analysis logic.

# 4. Push to Feishu (dry-run mode for preview, does not actually send)
node scripts/deliver.js --dry-run

# Actually send the message
node scripts/deliver.js --input /tmp/us-fund-result.json
```

**Using with Claude Code:**

Inside Claude Code, simply say:

> "Run today's US stock fund briefing"

Claude will automatically execute: collect data → AI analysis → push to Feishu.

### 5. Set up scheduled tasks (optional)

```bash
# macOS launchd
# Copy and edit the plist template, fill in your project path,
# then load it:
launchctl load ~/Library/LaunchAgents/com.usfundadvisor.daily.plist
```

Or use cron:

```bash
# Run daily at 06:00 Beijing Time
0 6 * * * /path/to/us-fund-advisor/scripts/run-daily.sh
```

## Data Sources

| Data Source | Status | Description |
|-------------|--------|-------------|
| **FRED Macro Data** | Stable | Official Federal Reserve data, including 7 core indicators: interest rates, CPI, employment, VIX, etc. |
| **Yahoo Finance** | Requires adaptation | Market data API, currently has anti-scraping restrictions; consider alternatives. |
| **RSS News** | Partially available | Depends on source site stability; can be customized. |
| **Twitter/X** | Requires config | Requires X API v2 Bearer Token. |
| **AKShare** | Optional | A-share fund NAVs, US stock historical data; requires Python environment. |

## Project Structure

```
us-fund-advisor/
├── README.md                 # This file (Chinese)
├── README.en.md              # English version of README
├── LICENSE                   # MIT License
├── package.json              # Node.js dependencies
├── config.template.json      # Config template (copy to config.json)
├── sources.json              # Data source config (X accounts, RSS, APIs, etc.)
├── funds.json                # Target fund list (customizable)
├── prompts/
│   └── daily-briefing.md     # Claude AI analysis prompt template
└── scripts/
    ├── generate-feed.js      # Central feed generator (pulls all data sources)
    ├── collect.js            # Data merging and preprocessing
    ├── deliver.js            # Feishu message card push
    ├── fetch_akshare.py      # AKShare data bridge (Python, optional)
    └── run-daily.sh          # Daily scheduled task script
```

## Customization

### Change tracked sectors or funds

Edit `funds.json` and modify the funds marked with `primary: true` to match your actual holdings.

### Add or remove data sources

Edit `sources.json`. You can add or remove:
- `fred_series`: Macro indicators
- `market_tickers`: Market tickers
- `rss_feeds`: News sources
- `twitter_accounts`: X accounts

### Adjust AI analysis style

Edit `prompts/daily-briefing.md` to modify the analysis framework, output format, and language style.

## Tech Stack

- **Node.js 18+**: Data collection, Feishu push
- **Claude AI**: Market analysis and strategy generation
- **FRED API**: Macroeconomic data
- **Feishu / Lark Webhook**: Message push
- **Python 3 + AKShare** (optional): A-share fund NAVs

## Disclaimer

This tool generates analysis based on publicly available information via AI and is for **reference only**. It does **not** constitute investment advice. Invest at your own risk.

## License

MIT
