# ETF Analytics Documentation

Welcome to the ETF Analytics documentation. This comprehensive tool helps you track and analyze ETF performance with automated data collection and metrics calculation.

## Overview

The ETF Analytics system provides:

- **Automated Data Collection**: Daily updates from Yahoo Finance
- **52-Week Analysis**: Track high/low points and key dates
- **Threshold Monitoring**: Monitor price decreases from peaks
- **Database Storage**: Organized data storage with SQLite
- **Validation**: Comprehensive data validation and error checking

## Getting Started

New to ETF Analytics? Start here:

1. [How to Run Scripts](how_to_run_scripts.md) - Step-by-step execution guide
2. [Installation](user-guide/installation.md) - Setup instructions
3. [Configuration](user-guide/configuration.md) - Customize your setup

## Key Features

### 📊 Data Collection
- Fetch historical price data (OHLCV)
- Support for multiple ETFs and stocks
- Automated daily updates via GitHub Actions

### 📈 Analytics
- 52-week high/low calculations
- Price decrease thresholds (10%, 15%, 20%, 25%, 30%)
- Historical performance tracking

### 🛡️ Data Validation
- ISIN code validation
- Duplicate detection
- Data consistency checks
- Comprehensive error handling

### 💾 Database Management
- SQLite database with optimized schema
- Foreign key relationships
- Indexed queries for performance
- Backup and recovery capabilities

## Current Tracked ETFs

- **Vanguard S&P 500 UCITS ETF** (VUAA.L)
  - ISIN: IE00BFMXXD54
  - Exchange: London Stock Exchange
  - Currency: USD

- **iShares NASDAQ 100 UCITS ETF** (CNDX.L)
  - ISIN: IE00B53SZB19
  - Exchange: London Stock Exchange
  - Currency: GBP

## Quick Commands

```bash
# Initialize everything from scratch
python -m analytics.database.init_db
python -m analytics.database.load_symbols
python -m analytics.etl.market_data_fetcher

# Update data only
python -m analytics.etl.market_data_fetcher

# Load new symbols
python -m analytics.database.load_symbols
```

## Architecture

The system is built with modern Python practices:

- **Modular Design**: Separate packages for analytics and website
- **Clean Interfaces**: Well-defined APIs between components
- **Robust Error Handling**: Comprehensive logging and validation
- **Scalable Structure**: Easy to add new ETFs and features

## Next Steps

- Explore the [Components](components/analytics.md) section to understand the system architecture
- Check the [API Reference](api/database.md) for detailed function documentation
- Visit [Development](development/contributing.md) to contribute to the project

## Support

- Review error logs for troubleshooting
- Check data validation for common issues
- Ensure all dependencies are properly installed
- Use DB Browser for SQLite to inspect data

---

Ready to get started? Head to the [How to Run Scripts](how_to_run_scripts.md) guide!