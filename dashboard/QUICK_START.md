# Quick Start Guide - Metabase Dashboard

## ✅ Step 1: Containers Running (DONE!)

You should see in Docker Desktop:
- `stock-market-postgres` - Running (healthy)
- `stock-market-metabase` - Running

## 📋 Step 2: Initialize Database

Open a new terminal and run:

```bash
# From project root
python dashboard/data-export/init_postgres_db.py
```

This creates:
- All database tables
- 10 dashboard views

## 🔄 Step 3: Sync Your Data

```bash
# Sync SQLite data to PostgreSQL
python dashboard/data-export/sqlite_to_postgres.py

# Export market insights
python dashboard/data-export/market_insights_to_db.py
```

## 🌐 Step 4: Access Metabase

1. **Open browser:** http://localhost:3000
2. **Wait 30-60 seconds** for Metabase to fully initialize
3. **Complete setup:**
   - Create admin account (email + password)
   - Choose language
   - Skip optional steps

## 🔌 Step 5: Connect to PostgreSQL

1. In Metabase, go to: **Settings** → **Admin** → **Databases**
2. Click **Add a database**
3. Fill in:
   - **Database type:** PostgreSQL
   - **Name:** Stock Market Dashboard
   - **Host:** `postgres` (or `localhost` if connecting from outside Docker)
   - **Port:** `5432`
   - **Database name:** `stock_market`
   - **Username:** `metabase`
   - **Password:** `metabase_password`
4. Click **Save**

## ✅ Step 6: Verify Connection

1. Metabase will test the connection
2. If successful, click **Sync database schema**
3. You should see:
   - **Tables:** symbols, etf_data, fear_greed_index, etc.
   - **Views:** vw_etf_data_with_symbols, vw_fear_greed_latest, etc.

## 🎨 Step 7: Build Dashboards!

1. Click **New** → **Question**
2. Select a view (e.g., `vw_fear_greed_latest`)
3. Choose visualization type
4. Create your dashboard!

---

## 🐛 Troubleshooting

### Metabase not loading?
- Wait 1-2 minutes for full initialization
- Check logs: `cd dashboard; docker-compose logs metabase`

### Can't connect to PostgreSQL?
- Verify containers are running: `cd dashboard; docker-compose ps`
- Try `localhost` instead of `postgres` in Metabase connection

### No data in views?
- Make sure you ran the sync scripts (Step 3)
- Check SQLite database exists: `analytics/database/etf_database.db`

---

## 📊 Available Views

- `vw_etf_data_with_symbols` - ETF prices with names
- `vw_latest_etf_prices` - Current prices
- `vw_fear_greed_latest` - Current Fear & Greed Index
- `vw_fear_greed_historical` - Last 30 days
- `vw_sp500_sector_performance` - Sector data
- `vw_sp500_top_companies` - Top companies
- `vw_etf_holdings_detail` - Holdings for pie charts
- `vw_etf_performance_summary` - Combined metrics

See `dashboard/docs/DATABASE_VIEWS.md` for details.

