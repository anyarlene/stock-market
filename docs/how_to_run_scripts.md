# How to Run Scripts

Comprehensive guide for running the ETF Analytics Dashboard scripts with the modular ETL workflow.

## Quick Start

### Run Complete Workflow
```bash
# From stock-market/ directory
python analytics/workflow.py
```

This single command executes the entire ETL pipeline:
1. Database initialization
2. Symbol loading
3. Market data fetching
4. Currency conversion
5. Data export

## Individual Step Execution

### 1. Database Initialization
```bash
python analytics/workflow.py --step init
```
**What it does:**
- Creates database with complete schema
- Sets up all tables and indices
- Includes currency_rates and EUR columns

### 2. Market Data Fetching
```bash
python analytics/workflow.py --step fetch
```
**What it does:**
- Fetches historical market data from 2021-12-01
- Downloads OHLCV data for all configured ETFs
- Stores data in SQLite database

### 3. Currency Conversion
```bash
python analytics/workflow.py --step currency
```
**What it does:**
- Converts USD/GBP prices to EUR
- Fetches historical exchange rates
- Updates database with EUR prices
- Caches exchange rates for performance

### 4. Data Export
```bash
python analytics/workflow.py --step export
```
**What it does:**
- Exports data to JSON format
- Generates files for website consumption
- Creates individual ETF files and combined data

## Direct Script Execution

### Market Data Fetcher
```bash
python analytics/etl/market_data_fetcher.py
```
**Use cases:**
- Test market data fetching independently
- Debug API connection issues
- Verify data source availability

### Currency Converter ETL
```bash
python analytics/etl/currency_converter_etl.py
```
**Use cases:**
- Test currency conversion logic
- Debug exchange rate fetching
- Verify EUR price calculations

### Data Exporter
```bash
python analytics/etl/data_exporter.py
```
**Use cases:**
- Test data export functionality
- Debug JSON generation
- Verify website data format

## Diagnostic Tools

### Database Diagnostics
```bash
python analytics/database_diagnostic.py
```
**What it shows:**
- All symbols in database
- Record counts per symbol
- EUR conversion status
- Currency rates stored
- Sample data verification

**Use cases:**
- Verify database state
- Debug conversion issues
- Check data integrity
- Monitor system health

## Testing Scenarios

### 1. New Installation
```bash
# Complete fresh setup
python analytics/workflow.py
```

### 2. Data Refresh
```bash
# Update market data only
python analytics/workflow.py --step fetch
python analytics/workflow.py --step currency
python analytics/workflow.py --step export
```

### 3. Currency Conversion Only
```bash
# Re-run currency conversion
python analytics/workflow.py --step currency
```

### 4. Export Only
```bash
# Regenerate website data
python analytics/workflow.py --step export
```

## Troubleshooting Commands

### Check Database Status
```bash
python analytics/database_diagnostic.py
```

### Test Individual Components
```bash
# Test market data fetching
python analytics/etl/market_data_fetcher.py

# Test currency conversion
python analytics/etl/currency_converter_etl.py

# Test data export
python analytics/etl/data_exporter.py
```

### Verify Data Quality
```bash
# Check database contents
python analytics/database_diagnostic.py

# Expected output:
# - 2 symbols loaded
# - ~929 records per symbol
# - All records have EUR data
# - Currency rates stored
```

## Performance Optimization

### Batch Processing
The system uses batch processing for efficiency:
- **Currency Conversion**: Processes multiple records at once
- **Rate Fetching**: Fetches rates for date ranges
- **Database Operations**: Bulk inserts and updates

### Caching Strategy
- **Exchange Rates**: Cached in database to avoid API calls
- **Database Connections**: Optimized connection management
- **Query Results**: Indexed for fast retrieval

## Error Handling

### Common Issues and Solutions

#### 1. ModuleNotFoundError
**Problem**: `ModuleNotFoundError: No module named 'analytics'`
**Solution**: Ensure you're in the `stock-market/` directory
```bash
cd stock-market
python analytics/workflow.py
```

#### 2. Database Connection Issues
**Problem**: Database file not found
**Solution**: Run database initialization
```bash
python analytics/workflow.py --step init
```

#### 3. Currency Conversion Failures
**Problem**: EUR columns remain NULL
**Solution**: Check and re-run conversion
```bash
python analytics/database_diagnostic.py
python analytics/workflow.py --step currency
```

#### 4. API Rate Limits
**Problem**: Yahoo Finance API errors
**Solution**: Wait and retry
```bash
# Wait 5 minutes, then retry
sleep 300
python analytics/workflow.py --step fetch
```

## Development Workflow

### 1. Adding New ETFs
```bash
# 1. Edit load_symbols.py
# 2. Test symbol loading
python analytics/workflow.py --step fetch

# 3. Test currency conversion
python analytics/workflow.py --step currency

# 4. Test data export
python analytics/workflow.py --step export
```

### 2. Modifying Currency Logic
```bash
# 1. Edit currency_converter.py
# 2. Test conversion
python analytics/etl/currency_converter_etl.py

# 3. Verify results
python analytics/database_diagnostic.py
```

### 3. Updating Website Data
```bash
# Regenerate website data
python analytics/workflow.py --step export

# Verify files created
ls -la website/data/
```

## Production Deployment

### Scheduled Updates
```bash
# Daily market data update (crontab)
0 18 * * 1-5 cd /path/to/stock-market && python analytics/workflow.py
```

### Database Backup
```bash
# Backup before updates
cp analytics/database/etf_database.db backup_$(date +%Y%m%d).db

# Run updates
python analytics/workflow.py

# Verify backup
python analytics/database_diagnostic.py
```

### Monitoring
```bash
# Check system health
python analytics/database_diagnostic.py

# Expected healthy output:
# - All symbols present
# - All records converted
# - Currency rates cached
# - No orphaned records
```

## Best Practices

### 1. Always Run from Root Directory
```bash
cd stock-market
python analytics/workflow.py
```

### 2. Test Individual Steps First
```bash
# Test before full workflow
python analytics/workflow.py --step fetch
python analytics/workflow.py --step currency
```

### 3. Use Diagnostics for Verification
```bash
# Verify after each major step
python analytics/database_diagnostic.py
```

### 4. Monitor Logs
```bash
# Check for errors and warnings
python analytics/workflow.py 2>&1 | tee workflow.log
```

### 5. Backup Before Major Changes
```bash
# Backup database
cp analytics/database/etf_database.db backup_$(date +%Y%m%d_%H%M%S).db
```

## Command Reference

### Workflow Commands
```bash
python analytics/workflow.py                    # Complete workflow
python analytics/workflow.py --step fetch      # Market data only
python analytics/workflow.py --step currency   # Currency conversion only
python analytics/workflow.py --step export     # Data export only
```

### Diagnostic Commands
```bash
python analytics/database_diagnostic.py        # Database status
```

### Direct Script Commands
```bash
python analytics/etl/market_data_fetcher.py    # Direct market data fetch
python analytics/etl/currency_converter_etl.py # Direct currency conversion
python analytics/etl/data_exporter.py          # Direct data export
```

This modular approach provides **flexibility, testability, and maintainability** while ensuring **reliable data processing** and **easy troubleshooting**.
