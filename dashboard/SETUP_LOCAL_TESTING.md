# Local Testing Guide

## Step-by-Step Setup

### Step 1: Navigate to Dashboard Directory

```bash
cd dashboard
```

**Important:** All docker-compose commands must be run from the `dashboard/` directory!

### Step 2: Start Docker Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Metabase (port 3000)

**Check if services are running:**
```bash
docker-compose ps
```

You should see both `postgres` and `metabase` services running.

### Step 3: Wait for Services to Start

Wait 30-60 seconds for Metabase to fully initialize. Check logs:

```bash
docker-compose logs metabase
```

Look for: "Metabase initialization complete" or similar message.

### Step 4: Initialize PostgreSQL Database

From the project root (not dashboard directory):

```bash
# Make sure you're in project root
cd /c/git/stock-market

# Initialize database
python dashboard/data-export/init_postgres_db.py
```

### Step 5: Sync Data from SQLite to PostgreSQL

```bash
# Sync main market data
python dashboard/data-export/sqlite_to_postgres.py

# Export market insights
python dashboard/data-export/market_insights_to_db.py
```

### Step 6: Access Metabase

1. Open browser: http://localhost:3000
2. Complete initial setup:
   - Create admin account (email + password)
   - Choose language
   - Skip optional steps

### Step 7: Connect Metabase to PostgreSQL

1. In Metabase, go to: **Settings** → **Admin** → **Databases**
2. Click **Add a database**
3. Fill in connection details:
   - **Database type:** PostgreSQL
   - **Name:** Stock Market Dashboard
   - **Host:** `postgres` (if running in Docker) or `localhost` (if connecting from outside Docker)
   - **Port:** `5432`
   - **Database name:** `stock_market`
   - **Username:** `metabase`
   - **Password:** `metabase_password`
4. Click **Save**

### Step 8: Verify Connection

1. Metabase will test the connection
2. If successful, you'll see the database listed
3. Click **Sync database schema** to load tables and views

### Step 9: Explore Data

1. Go to **Browse Data**
2. You should see:
   - Tables: `symbols`, `etf_data`, `fear_greed_index`, etc.
   - Views: `vw_etf_data_with_symbols`, `vw_fear_greed_latest`, etc.

### Step 10: Create Your First Dashboard

1. Click **New** → **Question**
2. Select a view (e.g., `vw_fear_greed_latest`)
3. Choose visualization type
4. Build your dashboard!

## Troubleshooting

### Docker Compose Not Found

If you get "command not found":
- Make sure Docker Desktop is installed and running
- Try: `docker compose up -d` (without hyphen, newer Docker versions)

### Port Already in Use

If port 3000 or 5432 is already in use:

Edit `dashboard/docker-compose.yml` and change ports:
```yaml
ports:
  - "3001:3000"  # Change 3000 to 3001
  - "5433:5432"  # Change 5432 to 5433
```

### PostgreSQL Connection Failed

If Metabase can't connect:
1. Check PostgreSQL is running: `docker-compose ps`
2. Check logs: `docker-compose logs postgres`
3. Try connecting with `localhost` instead of `postgres` in Metabase

### Database Not Initialized

If you see "relation does not exist" errors:
1. Make sure you ran: `python dashboard/data-export/init_postgres_db.py`
2. Check for errors in the output
3. Verify PostgreSQL is running: `docker-compose ps`

### No Data in Views

If views are empty:
1. Run sync: `python dashboard/data-export/sqlite_to_postgres.py`
2. Check SQLite database exists: `analytics/database/etf_database.db`
3. Verify data in SQLite first

## Useful Commands

### Stop Services
```bash
cd dashboard
docker-compose down
```

### View Logs
```bash
cd dashboard
docker-compose logs -f  # Follow logs
docker-compose logs metabase  # Metabase logs only
docker-compose logs postgres  # PostgreSQL logs only
```

### Restart Services
```bash
cd dashboard
docker-compose restart
```

### Remove Everything (Careful!)
```bash
cd dashboard
docker-compose down -v  # Removes volumes (deletes data!)
```

### Check Service Status
```bash
cd dashboard
docker-compose ps
```

## Quick Test Checklist

- [ ] Docker Desktop is running
- [ ] Navigated to `dashboard/` directory
- [ ] `docker-compose up -d` succeeded
- [ ] Services are running (`docker-compose ps`)
- [ ] Database initialized (`init_postgres_db.py`)
- [ ] Data synced (`sqlite_to_postgres.py`)
- [ ] Market insights exported (`market_insights_to_db.py`)
- [ ] Metabase accessible at http://localhost:3000
- [ ] PostgreSQL connection configured in Metabase
- [ ] Tables and views visible in Metabase

## Next Steps

Once everything is working:
1. Create dashboards using the views
2. Set up auto-refresh schedules
3. Share dashboards (optional)
4. Test daily workflow integration

