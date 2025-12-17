# Metabase Dashboard Setup

This directory contains the setup and scripts for the Metabase dashboard that visualizes market insights data.

## Overview

The dashboard uses:
- **Metabase** - Open-source business intelligence tool
- **PostgreSQL** - Database for dashboard data
- **Docker Compose** - Easy deployment

## Quick Start

### 1. Prerequisites

- Docker Desktop installed
- Python 3.12+ with dependencies installed (`pip install -r requirements.txt`)

### 2. Start Services

```bash
cd dashboard
docker-compose up -d
```

This starts:
- PostgreSQL on port `5432`
- Metabase on port `3000`

### 3. Initialize Database

```bash
python dashboard/data-export/init_postgres_db.py
```

This creates:
- Database schema (tables)
- Dashboard views (for easier querying)

### 4. Sync Data

```bash
# Sync SQLite data to PostgreSQL
python dashboard/data-export/sqlite_to_postgres.py

# Export market insights to PostgreSQL
python dashboard/data-export/market_insights_to_db.py
```

### 5. Access Metabase

1. Open browser: http://localhost:3000
2. Complete initial setup (create admin account)
3. Add PostgreSQL database connection:
   - Host: `postgres` (or `localhost` if running outside Docker)
   - Port: `5432`
   - Database: `stock_market`
   - Username: `metabase`
   - Password: `metabase_password`

### 6. Create Dashboards

Use the views created in the database:
- `vw_etf_data_with_symbols` - ETF price data with symbol names
- `vw_latest_etf_prices` - Latest prices for each ETF
- `vw_fear_greed_latest` - Current Fear & Greed Index
- `vw_fear_greed_historical` - Historical Fear & Greed Index (30 days)
- `vw_sp500_sector_performance` - S&P 500 sector performance
- `vw_sp500_top_companies` - Top S&P 500 companies
- `vw_etf_holdings_detail` - ETF holdings for pie charts
- `vw_etf_performance_summary` - Combined ETF performance metrics

## Daily Updates

The dashboard is automatically updated via GitHub Actions workflow:

1. **SQLite → PostgreSQL Sync** - Runs after market data update
2. **Market Insights Export** - Exports Fear & Greed, S&P 500, ETF holdings

The workflow runs Monday-Friday at 21:15 UTC (10:15 PM Berlin time).

## Manual Updates

If you need to update data manually:

```bash
# Sync all SQLite data to PostgreSQL
python dashboard/data-export/sqlite_to_postgres.py

# Export market insights
python dashboard/data-export/market_insights_to_db.py
```

## Environment Variables

You can customize PostgreSQL connection via environment variables:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=stock_market
export POSTGRES_USER=metabase
export POSTGRES_PASSWORD=metabase_password
```

Or create a `.env` file in the `dashboard/` directory.

## Stopping Services

```bash
cd dashboard
docker-compose down
```

To remove all data (careful!):

```bash
docker-compose down -v
```

## Troubleshooting

### Metabase won't connect to PostgreSQL

- Check PostgreSQL is running: `docker ps`
- Verify connection details match `docker-compose.yml`
- Check logs: `docker-compose logs postgres`

### Data not syncing

- Verify SQLite database exists: `analytics/database/etf_database.db`
- Check PostgreSQL connection: `python dashboard/data-export/init_postgres_db.py`
- Review logs for errors

### Views not showing in Metabase

- Re-run view creation: `python dashboard/data-export/init_postgres_db.py`
- Refresh database in Metabase: Settings → Databases → Sync database schema

## Files Structure

```
dashboard/
├── docker-compose.yml              # Docker setup
├── data-export/
│   ├── postgresql_schema.sql       # Database schema
│   ├── dashboard_views.sql        # Dashboard views
│   ├── init_postgres_db.py        # Initialize database
│   ├── sqlite_to_postgres.py      # Sync SQLite → PostgreSQL
│   └── market_insights_to_db.py   # Export market insights
├── docs/                           # Documentation
└── README.md                       # This file
```

## Next Steps

1. **Create Dashboards in Metabase:**
   - Fear & Greed Index gauge chart
   - S&P 500 sector performance
   - ETF holdings distribution
   - Market trends over time

2. **Set Up Auto-Refresh:**
   - Configure Metabase to auto-refresh dashboards
   - Set refresh intervals (e.g., daily at 10:30 PM)

3. **Share Dashboards:**
   - Create public links for sharing
   - Set up email subscriptions (optional)

## Support

For issues or questions, check:
- `METABASE_RECOMMENDATION.md` - Why we chose Metabase
- `POSTGRESQL_VS_DATABRICKS.md` - Database comparison
- Main project README.md

