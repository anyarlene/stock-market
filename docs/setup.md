# Setup Guide

Complete setup instructions for the ETF Analytics Dashboard with currency conversion and modular ETL workflow.

## Prerequisites

- **Python 3.8+** (recommended: Python 3.10+)
- **Git** for repository cloning
- **Internet connection** for data fetching

## Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd stock-market
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv market-env

# Activate virtual environment
# On Windows:
market-env\Scripts\activate

# On macOS/Linux:
source market-env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Quick Start

### Run Complete ETL Workflow
```bash
# From stock-market/ directory
python analytics/workflow.py
```

This single command will:
1. Initialize the database with complete schema
2. Load ETF symbols (VUAA.L, CNDX.L)
3. Fetch market data from 2021-12-01 onwards
4. Convert USD/GBP prices to EUR using historical rates
5. Export data for the website

### View Dashboard
Open `website/index.html` in your web browser to see the interactive dashboard.

## Testing Individual Components

### Test Currency Conversion Only
```bash
python analytics/workflow.py --step currency
```

### Test Data Export Only
```bash
python analytics/workflow.py --step export
```

### Test Market Data Fetching Only
```bash
python analytics/workflow.py --step fetch
```

## Database Diagnostics

### Check Database Status
```bash
python analytics/database_diagnostic.py
```

This will show:
- All symbols in the database
- Record counts per symbol
- EUR conversion status
- Currency rates stored
- Sample data verification

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError
**Problem**: `ModuleNotFoundError: No module named 'analytics'`
**Solution**: Ensure you're running commands from the `stock-market/` directory, not from inside `analytics/`

#### 2. Database Connection Issues
**Problem**: Database file not found or permission errors
**Solution**: 
```bash
# Check if database directory exists
ls -la analytics/database/

# Ensure write permissions
chmod 755 analytics/database/
```

#### 3. Currency Conversion Failures
**Problem**: EUR columns remain NULL
**Solution**:
```bash
# Run diagnostic to check status
python analytics/database_diagnostic.py

# Re-run currency conversion
python analytics/workflow.py --step currency
```

#### 4. API Rate Limits
**Problem**: Yahoo Finance API errors
**Solution**: Wait a few minutes and retry, or check your internet connection

### Performance Optimization

#### For Large Datasets
- The system uses batch processing for currency conversion
- Exchange rates are cached to avoid repeated API calls
- Database indexing optimizes query performance

#### Memory Usage
- SQLite database is efficient for this scale
- Batch processing prevents memory overflow
- Data is processed in chunks

## Configuration

### Database Location
- **Default**: `analytics/database/etf_database.db`
- **Backup**: Copy the `.db` file to preserve data

### Data Sources
- **Market Data**: Yahoo Finance (via `yfinance`)
- **Exchange Rates**: Yahoo Finance currency pairs
- **Historical Period**: 2021-12-01 to present

### Supported ETFs
- **Vanguard S&P 500 UCITS ETF (VUAA.L)** - USD
- **iShares NASDAQ 100 UCITS ETF (CNDX.L)** - GBP

## Development Setup

### Adding New ETFs
1. Edit `analytics/database/load_symbols.py`
2. Add new symbol with correct currency
3. Run `python analytics/workflow.py --step fetch`
4. Test with `python analytics/workflow.py --step currency`

### Extending Features
- **New Metrics**: Modify `analytics/etl/market_data_fetcher.py`
- **Additional Currencies**: Extend `analytics/utils/currency_converter.py`
- **UI Changes**: Edit `website/js/app.js`

## Production Deployment

### Database Backup
```bash
# Backup database
cp analytics/database/etf_database.db backup_$(date +%Y%m%d).db
```

### Scheduled Updates
```bash
# Add to crontab for daily updates
0 18 * * 1-5 cd /path/to/stock-market && python analytics/workflow.py
```

### Web Server Setup
- Copy `website/` directory to your web server
- Ensure `data/` directory is writable
- Configure CORS if needed for API access

## Verification

### Check Data Quality
```bash
# Run diagnostic
python analytics/database_diagnostic.py

# Expected output:
# - 2 symbols loaded
# - ~929 records per symbol
# - All records have EUR data
# - Currency rates stored
```

### Test Website
1. Open `website/index.html`
2. Select an ETF from dropdown
3. Verify chart displays correctly
4. Test currency toggle (EUR/USD)
5. Check profit targets functionality

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Run `python analytics/database_diagnostic.py` for diagnostics
3. Review logs for error messages
4. Ensure all prerequisites are met
