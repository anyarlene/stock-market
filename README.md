# ETF Analytics Dashboard

ETF analytics platform with automated market data updates, currency conversion, and interactive visualizations.

## Features

- Historical market data from 2021-12-01 onwards
- Automatic USD/GBP to EUR conversion with historical rates
- Interactive charts with time range filtering
- 52-week high/low metrics and entry point analysis
- Automated daily updates via GitHub Actions

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

### View Dashboard

Open `website/index.html` in your browser.

### Investment Strategy Planner

Access the interactive investment strategy planner at `website/investment-strategy.html` to:
- Plan lump-sum investments by region
- View ETF purchase plans with real-time prices
- Analyze historical growth and projections
- Assess risk scenarios and tax implications

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
