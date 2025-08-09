# How to Run ETF Analytics Scripts

This guide explains how to run the ETF analytics scripts in the correct order to set up and maintain your database.

## Prerequisites

Before running any scripts, ensure you have:
1. Python 3.10 or higher installed
2. Created and activated a virtual environment
3. Installed all required dependencies

```bash
# Create virtual environment
python -m venv market-env

# Activate virtual environment (Windows Git Bash)
source market-env/Scripts/activate

# Install dependencies
pip install -r requirements.txt
```

## Script Execution Order

### 1. Database Initialization

Initialize the database schema and create all tables:

```bash
python -m analytics.database.init_db
```

**What it does:**
- Creates the SQLite database file
- Sets up all database tables (symbols, etf_data, fifty_two_week_metrics, decrease_thresholds)
- Creates necessary indexes for performance

### 2. Load Symbols

Load ETF/stock symbols into the database:

```bash
python -m analytics.database.load_symbols
```

**What it does:**
- Reads symbols from `analytics/database/reference/symbols.csv`
- Validates ISIN codes, tickers, and other data
- Loads symbols into the database
- Verifies data consistency between CSV and database

### 3. Fetch Market Data

Fetch historical market data and calculate metrics:

```bash
python -m analytics.etl.market_data_fetcher
```

**What it does:**
- Fetches 1 year of historical data from Yahoo Finance
- Stores OHLCV data in the database
- Calculates 52-week high/low metrics
- Calculates entry points (10%, 15%, 20%, 25%, 30%) from 52-week high
- Provides detailed logging of the process

## Daily Operations

### Automated Updates

The project includes GitHub Actions for daily updates:
- Runs automatically at 22:00 UTC on weekdays
- Fetches latest market data
- Updates metrics and thresholds
- Commits changes to the repository

### Manual Updates

To manually update data:

```bash
python -m analytics.etl.market_data_fetcher
```

## Data Verification

Use these SQL queries in DB Browser for SQLite to verify your data:

### Check Symbols
```sql
SELECT * FROM symbols;
```

### Check Market Data
```sql
SELECT 
    s.name,
    COUNT(*) as data_points,
    MIN(date) as earliest_date,
    MAX(date) as latest_date
FROM etf_data e
JOIN symbols s ON s.id = e.symbol_id
GROUP BY s.name;
```

### Check 52-Week Metrics
```sql
SELECT 
    s.name,
    m.calculation_date,
    m.high_52week,
    m.low_52week,
    m.high_date,
    m.low_date
FROM fifty_two_week_metrics m
JOIN symbols s ON s.id = m.symbol_id
ORDER BY s.name, m.calculation_date DESC;
```

### Check Entry Points
```sql
SELECT 
    s.name,
    d.calculation_date,
    d.high_52week_price,
    d.decrease_10_price,
    d.decrease_20_price,
    d.decrease_30_price
FROM decrease_thresholds d
JOIN symbols s ON s.id = d.symbol_id
ORDER BY s.name, d.calculation_date DESC;
```

## Adding New Symbols

To add new ETFs or stocks:

1. Edit `analytics/database/reference/symbols.csv`
2. Add new row with: isin, ticker, name, asset_type, exchange, currency
3. Run the load symbols script: `python -m analytics.database.load_symbols`
4. Fetch data for new symbols: `python -m analytics.etl.market_data_fetcher`

## Troubleshooting

### Database Lock Errors
- Close DB Browser for SQLite completely
- Ensure no other processes are using the database
- Scripts include retry logic for temporary locks

### Missing Data
- Check internet connection for Yahoo Finance API
- Verify ticker symbols are correct
- Check logs for detailed error messages

### Validation Errors
- Ensure ISIN codes follow correct format (2 letters + 9 alphanumeric + 1 digit)
- Verify all required CSV columns are present
- Check for duplicate entries in CSV

## File Structure

```
analytics/
├── database/
│   ├── init_db.py          # Database initialization
│   ├── load_symbols.py     # Symbol loading script
│   ├── db_manager.py       # Database operations
│   ├── schema.sql          # Database schema
│   ├── reference/
│   │   └── symbols.csv     # ETF/stock symbols configuration
│   └── etf_database.db     # SQLite database file
├── etl/
│   ├── market_data_fetcher.py  # Market data fetching
│   └── data_exporter.py        # Export data to JSON for website
└── utils/
    └── validators.py       # Data validation utilities

website/
├── index.html              # Main dashboard page
├── css/
│   └── style.css          # Dashboard styling
├── js/
│   └── app.js            # Chart.js dashboard logic
└── data/                 # Generated JSON data files
    ├── symbols.json      # Available ETFs list
    ├── etf_data.json     # Combined ETF data
    ├── vuaa.l.json       # Vanguard S&P 500 data
    └── cndx.l.json       # iShares NASDAQ 100 data
```

## 5. Generate Website Data

Before running the website, you need to export data from the database to JSON files:

```bash
# Export ETF data to JSON files for the website
python -m analytics.etl.data_exporter
```

**Expected output:**
```
Starting data export for website...
Exporting data for Vanguard S&P 500 UCITS ETF (VUAA.L)...
Exporting data for iShares NASDAQ 100 UCITS ETF (CNDX.L)...
✅ Data export completed! Files created in website/data/
   - etf_data.json (combined data)
   - symbols.json (symbols list)
   - vuaa.l.json
   - cndx.l.json
```

**Verification:**
```bash
# Check generated files
ls website/data/
```

## 6. Run the Website Locally

### Option A: Local Access Only
```bash
# Navigate to website directory
cd website

# Start local server
python -m http.server 8000
```

### Option B: Network Access (Multiple Devices)
```bash
# Navigate to website directory
cd website

# Start server accessible from other devices on same WiFi
python -m http.server 8000 --bind 0.0.0.0
```

**Access URLs:**
- **Local machine:** http://localhost:8000
- **Other devices on same WiFi:** http://YOUR_IP_ADDRESS:8000
  - To find your IP: `ipconfig | findstr IPv4` (Windows) or `hostname -I` (Linux/Mac)

**What you'll see:**
- ETF Analytics Dashboard with dropdown selector
- Interactive Chart.js visualization showing:
  - Price evolution over 3 months
  - 52-week high/low reference lines
  - Entry point markers (10%, 15%, 20%, 25%, 30%) from 52-week high
- Metrics panel with 52-week high/low values
- Threshold cards showing target prices

**To stop the server:** Press `Ctrl+C` in the terminal

## Network Access Notes

- **Same WiFi:** Other laptops can access via your IP address
- **Different WiFi:** Copy the `website/` folder to the other machine and run locally
- **Future:** Deploy to GitHub Pages for global access

## Data Update Workflow

For daily updates, run these commands in sequence:

```bash
# 1. Fetch latest market data
python -m analytics.etl.market_data_fetcher

# 2. Export updated data for website
python -m analytics.etl.data_exporter

# 3. Website will automatically show updated data on refresh
```
