# Setup Guide

This guide will help you set up the Stock Market Analytics project from scratch. The project tracks ETF prices, calculates 52-week metrics, and visualizes entry points from 52-week highs.

## Prerequisites

- Python 3.10 or higher
- Git Bash (recommended for Windows users)
- Internet connection for downloading dependencies

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd stock-market
```

## Step 2: Environment Setup

### Create Virtual Environment

```bash
# Create the market-env virtual environment
python -m venv market-env

# Activate the environment (Windows Git Bash)
source market-env/Scripts/activate

# Activate the environment (Linux/Mac)
source market-env/bin/activate
```

### Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pandas, yfinance, sqlalchemy; print('Dependencies installed successfully!')"
```

## Step 3: Database Setup

### Initialize Database

```bash
# Initialize the SQLite database
python -m analytics.database.init_db
```

### Load ETF Symbols

```bash
# Load configured ETF symbols
python -m analytics.database.load_symbols
```

## Step 4: Fetch Market Data

```bash
# Fetch historical market data for configured ETFs
python -m analytics.etl.market_data_fetcher
```

### Export Data for Website

```bash
# Export processed data to JSON format for the website
python -m analytics.etl.data_exporter
```

## Step 5: Launch Web Dashboard

### Navigate to Website Directory

```bash
cd website
```

### Start Local Server

**Option A: Local Access Only**
```bash
python -m http.server 8000
```

**Option B: Network Access (Multi-device)**
```bash
python -m http.server 8000 --bind 0.0.0.0
```

### Access the Dashboard

- **Local:** http://localhost:8000
- **Network:** http://YOUR_IP_ADDRESS:8000 (same WiFi devices)

## Step 6: Verify Setup

### Check Database

Use DB Browser for SQLite to open `analytics/database/etf_database.db` and verify:
- Symbols table contains ETF information
- ETF data table contains historical prices
- 52-week metrics are calculated

### Check Website Data

Verify that `website/data/` contains:
- `etf_data.json` - Main ETF data
- `symbols.json` - ETF symbol information
- Individual ETF files (e.g., `vuaa.l.json`, `cndx.l.json`)

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the correct virtual environment
2. **Database Errors**: Check that the database file exists and has proper permissions
3. **Data Fetching Errors**: Verify internet connection and Yahoo Finance API availability
4. **Website Not Loading**: Check that the server is running on the correct port

### Environment Variables (Optional)

Create a `.env` file in the project root for custom configuration:

```env
DATABASE_PATH=analytics/database/etf_database.db
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Next Steps

- Read the [Script Execution Guide](how_to_run_scripts.md) for detailed script usage
- Explore the analytics modules to understand the data processing pipeline
- Check the [Project Overview](../../README.md) for general project information
