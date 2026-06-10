# ETF Analytics Dashboard — v1

ETF analytics platform with automated market data updates, dbt transformations,
and a Metabase dashboard built by AI.

## Stack

| Layer | Tool |
|---|---|
| Data fetch | Python + `yfinance` |
| Database | PostgreSQL 16 (Docker) |
| Transformations | dbt Core |
| Visualization | Metabase OSS (Docker) |
| Orchestration | GitHub Actions |

## Supported ETFs

| Ticker | Name | Currency |
|---|---|---|
| VOO | Vanguard S&P 500 ETF | USD |
| VTI | Vanguard Total Stock Market ETF | USD |
| QQQ | Invesco QQQ Trust | USD |
| VUAA.L | Vanguard S&P 500 UCITS ETF | USD |
| CNDX.L | iShares NASDAQ 100 UCITS ETF | GBP |

---

## Quick Start (Docker Desktop required)

```bash
# 1. Clone and configure
git clone <repository-url>
cd stock-market
cp .env.example .env          # defaults work for local Docker

# 2. Start PostgreSQL + Metabase
docker compose up -d

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Initialize DB, load symbols, fetch data
cd analytics
PYTHONPATH=.. python database/init_db.py
PYTHONPATH=.. python database/load_symbols.py
cd ..
PYTHONPATH=. python analytics/enhanced_workflow.py --step full

# 5. Run dbt transformations
cd dbt
dbt run --profiles-dir .
cd ..

# 6. Open Metabase at http://localhost:3000
```

For Metabase setup, MCP connection, and AI-assisted dashboard build:
→ See `analytics/docs/metabase_setup.md`

---

## dbt Models

```
dbt/models/
├── staging/
│   ├── stg_etf_data.sql          ← cleans raw price + symbol join
│   └── stg_currency_rates.sql    ← cleans FX rate cache
├── intermediate/
│   └── int_etf_eur.sql           ← ensures all rows have EUR prices
└── marts/
    ├── mart_price_history.sql    ← daily OHLCV + EUR + derived metrics
    ├── mart_52week_metrics.sql   ← latest 52-week high/low per ETF
    └── mart_entry_thresholds.sql ← 5–30% entry levels (long format)
```

Run transformations:
```bash
cd dbt && dbt run --profiles-dir . && dbt test --profiles-dir .
```

---

## Automation

### Production — zero daily work, access from anywhere

| Piece | Service | Cost |
|---|---|---|
| Database | [Supabase](https://supabase.com) free tier | Free |
| Daily data update | GitHub Actions (already configured) | Free |
| Dashboard | Oracle Cloud Always Free VM | Free |

**After one-time setup:** open `http://<oracle-ip>:3000` from any browser.
Data refreshes automatically every weekday. No local Docker. No manual runs.

→ Full setup guide: `analytics/docs/metabase_setup.md` (Production Setup section)

### GitHub Actions schedule

- **When**: Weekdays at 21:15 UTC
- **What**: ETL fetch → PostgreSQL insert → `dbt run` → `dbt test`
- **Required secret**: `DATABASE_URL` (Supabase connection string) in repo Settings → Secrets

### Development Workflow

```bash
git checkout -b cursor/<feature-name>-7a1c
# make changes
git push -u origin <branch>
# open PR → merge to main
```

---

## Project Structure

```
stock-market/
├── analytics/
│   ├── enhanced_workflow.py        # ETL orchestrator
│   ├── database/                   # DB manager + schema (PostgreSQL)
│   ├── etl/                        # Fetchers + currency ETL
│   ├── utils/                      # Currency converter
│   └── docs/                       # Setup + Metabase guide
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/
│       ├── intermediate/
│       └── marts/
├── website/
│   ├── index.html                  # Legacy chart view (kept)
│   └── archived/                   # Investment Strategy Planner (archived)
├── .github/workflows/
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

---

## Documentation

| File | Topic |
|---|---|
| `analytics/docs/metabase_setup.md` | Full Metabase + MCP + AI dashboard guide |
| `analytics/docs/stock-market-v1.md` | v1 plan and architecture overview |
| `analytics/docs/setup.md` | Initial environment setup |
| `analytics/docs/automation_setup.md` | GitHub Actions configuration |

---

## Adding New ETFs

1. Edit `analytics/database/reference/symbols.csv`
2. Run `python analytics/database/load_symbols.py`
3. Run `python analytics/enhanced_workflow.py --step incremental`
4. Run `cd dbt && dbt run --profiles-dir .`
5. Refresh Metabase metadata sync (Admin > Databases > Sync)
