# ETF Analytics Dashboard

ETF analytics platform with automated market data updates, currency conversion, and interactive visualizations.

## Features

- Historical market data from 2021-12-01 onwards
- Automatic USD/GBP to EUR conversion with historical rates
- Interactive charts with time range filtering
- 52-week high/low metrics and entry point analysis
- Automated daily updates via GitHub Actions
- **ETF Insights Explorer** - Market sentiment, sector performance, and ETF holdings analysis

## Supported ETFs

### UCITS ETFs (European-listed)
- Vanguard S&P 500 UCITS ETF (VUAA.L) - USD
- iShares NASDAQ 100 UCITS ETF (CNDX.L) - GBP

### US-listed ETFs
- Vanguard S&P 500 ETF (VOO) - USD
- Vanguard Total Stock Market ETF (VTI) - USD
- Invesco QQQ Trust (QQQ) - USD

## Quick Start

### Installation

```bash
git clone <repository-url>
cd stock-market
python -m venv market-env
source market-env/bin/activate  # Windows: market-env\Scripts\activate
pip install -r requirements.txt
```

### Run Complete Workflow

```bash
python analytics/enhanced_workflow.py --step full
```

This runs: database init → load symbols → fetch data → convert currencies → export data

### Run Individual Steps

```bash
python analytics/enhanced_workflow.py --step incremental  # Daily updates
python analytics/enhanced_workflow.py --step currency      # Currency conversion
python analytics/enhanced_workflow.py --step export      # Export website data
```

### View Dashboards

- **ETF Analytics Dashboard**: Open `website/index.html` in your browser
- **ETF Insights Explorer**: Open `website/market-insights.html` for market sentiment, sector performance, and ETF holdings analysis

### Investment Strategy Planner

Access the interactive investment strategy planner at `website/investment-strategy.html` to:
- Plan lump-sum investments by region
- View ETF purchase plans with real-time prices
- Analyze historical growth and projections
- Assess risk scenarios and tax implications

## ETF Insights Explorer

The **ETF Insights Explorer** dashboard provides comprehensive market analysis with three key visualizations:

### Features

1. **Fear & Greed Index**
   - Real-time market sentiment indicator (0-100 scale)
   - Historical trend visualization
   - Classification: Extreme Fear, Fear, Neutral, Greed, Extreme Greed
   - Data source: CNN Fear & Greed Index

2. **S&P 500 Sector Performance**
   - Interactive sector heatmap showing 1-month performance
   - Sector-by-sector breakdown with change percentages
   - Sortable sector cards
   - Data source: Yahoo Finance via SPDR sector ETFs

3. **ETF Holdings Distribution**
   - Interactive pie charts showing top holdings for major ETFs
   - Detailed holdings table with percentages
   - Supports: VOO, QQQ, VTI, VUAA.L, CNDX.L
   - Data source: Yahoo Finance

### Generating Market Insights Data

To generate the data files for the ETF Insights Explorer:

```bash
# Export market insights data (Fear & Greed Index, S&P 500 sectors, ETF holdings)
python -m analytics.etl.market_insights_fetcher
```

This creates the following files in `website/data/`:
- `fear_greed_index.json` - Current and historical Fear & Greed Index data
- `sp500_sectors.json` - S&P 500 sector performance data
- `etf_holdings.json` - Holdings data for supported ETFs

### Testing the Dashboard Locally

**Quick Start:**
1. Install the required package: `pip install fear-greed-index`
2. Generate data: `python -m analytics.etl.market_insights_fetcher`
3. Start a local server: `cd website && python -m http.server 8000`
4. Open in browser: `http://localhost:8000/market-insights.html`

For detailed testing instructions, see `analytics/docs/market_insights_setup.md`

![ETF Insights Explorer Dashboard](website/screenshots/market-insights-dashboard.png)

*Note: Screenshot placeholder - add your dashboard screenshot here*

## Automation

### Production (GitHub Actions)

- **Schedule**: Weekdays at 21:15 UTC
- **Process**: Incremental update → diagnostics → website export → auto-commit
- **Branch**: `main` only
- **Monitoring**: GitHub Actions tab

### Local Testing (Airflow - Optional)

- **Purpose**: Test workflows locally before production
- **Setup**: See `analytics/docs/airflow_setup.md`
- **Note**: Runs locally with Docker, no cloud costs

### Development Workflow

1. Create feature branch: `git checkout -b feature/my-update`
2. Make changes and test locally
3. Push to feature branch (triggers test automation)
4. Create pull request and merge to `main`
5. Production automation runs automatically on `main`

## Project Structure

```
stock-market/
├── analytics/                    # ETL pipeline
│   ├── enhanced_workflow.py     # Main orchestrator
│   ├── database/                # Database operations
│   ├── etl/                      # Data processing
│   └── docs/                     # Documentation
├── .github/workflows/           # GitHub Actions
│   ├── test_automation.yml      # CI testing
│   ├── production_automation.yml # Production automation
│   └── deploy-website.yml       # Website deployment
├── airflow/                      # Local Airflow setup (optional)
├── website/                      # Frontend dashboard
└── requirements.txt              # Dependencies
```

## Documentation

- `analytics/docs/setup.md` - Initial setup guide
- `analytics/docs/how_to_run_scripts.md` - Script execution guide
- `analytics/docs/automation_setup.md` - Automation configuration
- `analytics/docs/airflow_setup.md` - Local Airflow setup

## Configuration

- **Database**: `analytics/database/etf_database.db`
- **Data Source**: Yahoo Finance via `yfinance`
- **Historical Period**: 2021-12-01 to present

## Testing

```bash
# Database diagnostics
python analytics/database_diagnostic.py

# Test workflow components
python analytics/test_enhanced_workflow.py
```

## Adding New ETFs

1. Edit `analytics/database/reference/symbols.csv`
2. Run `python analytics/database/load_symbols.py`
3. Run `python analytics/enhanced_workflow.py --step incremental`
