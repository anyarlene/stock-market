# ETF Analytics and Visualization

A comprehensive tool for ETF analytics and visualization. Track ETF prices, calculate 52-week metrics, and visualize price movements with decrease thresholds.

## Features

- **ETF Price Tracking**: Daily price updates for configured ETFs
- **52-Week Metrics**: Track high/low points and important dates
- **Decrease Thresholds**: Monitor 10%, 15%, 20%, 25%, and 30% decreases from 52-week high
- **Interactive Web Dashboard**: Chart.js visualization with ETF switching and threshold monitoring
- **Multi-Device Access**: Local server accessible from multiple devices on same network
- **Automated Updates**: Daily data updates via GitHub Actions

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd stock-market

# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Initialize database
python -m analytics.database.init_db

# Load symbols
python -m analytics.database.load_symbols

# Fetch market data
python -m analytics.etl.market_data_fetcher

# Export data for website
python -m analytics.etl.data_exporter
```

### 3. Launch Web Dashboard

```bash
# Navigate to website directory
cd website

# Start local server (Option A: Local only)
python -m http.server 8000

# OR start server with network access (Option B: Multi-device)
python -m http.server 8000 --bind 0.0.0.0
```

**Access the dashboard:**
- **Local:** http://localhost:8000
- **Network:** http://YOUR_IP_ADDRESS:8000 (same WiFi devices)

### 4. Verify Data

Use DB Browser for SQLite to open `data/etf_database.db` and verify your data is loaded correctly.

## Project Structure

```
stock-market/
├── analytics/                  # Core analytics package
│   ├── database/              # Database management
│   │   ├── init_db.py         # Database initialization
│   │   ├── load_symbols.py    # Symbol loading
│   │   ├── db_manager.py      # Database operations
│   │   └── schema.sql         # Database schema
│   ├── etl/                   # ETL processes
│   │   └── market_data_fetcher.py  # Data pipeline
│   ├── models/                # Analytics models
│   └── utils/                 # Utility functions
│       └── validators.py      # Data validation
├── website/                   # Web dashboard
│   ├── index.html             # Main dashboard page
│   ├── css/style.css          # Dashboard styling
│   ├── js/app.js             # Chart.js visualization
│   └── data/                 # Generated JSON files
├── data/                      # Data storage
│   ├── reference/
│   │   └── symbols.csv        # ETF symbols configuration
│   └── etf_database.db       # SQLite database
├── docs/                      # Documentation
│   └── how_to_run_scripts.md  # Script execution guide
├── tests/                     # Test suite
└── .github/                   # CI/CD configuration
    └── workflows/
        └── update_etf_data.yml
```

## Current ETFs

The system currently tracks:
- **Vanguard S&P 500 UCITS ETF** (VUAA.L) - ISIN: IE00BFMXXD54
- **iShares NASDAQ 100 UCITS ETF** (CNDX.L) - ISIN: IE00B53SZB19

## Configuration

### Adding New ETFs

Edit `data/reference/symbols.csv` to add new ETFs:

```csv
isin,ticker,name,asset_type,exchange,currency
IE00BFMXXD54,VUAA.L,Vanguard S&P 500 UCITS ETF,ETF,LSE,USD
IE00B53SZB19,CNDX.L,iShares NASDAQ 100 UCITS ETF,ETF,LSE,GBP
```

### Environment Variables

Create a `.env` file (optional):

```env
DATABASE_PATH=data/etf_database.db
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Data Updates

### Automated Updates

Data is automatically updated daily at 22:00 UTC via GitHub Actions on weekdays.

### Manual Updates

```bash
# Fetch latest market data
python -m analytics.etl.market_data_fetcher

# Export updated data for website
python -m analytics.etl.data_exporter

# Refresh your browser to see updated dashboard
```

## Database Schema

The system uses SQLite with the following tables:

- **symbols**: ETF/stock information (ISIN, ticker, name, etc.)
- **etf_data**: Historical OHLCV price data
- **fifty_two_week_metrics**: 52-week high/low calculations
- **decrease_thresholds**: Price decrease thresholds from 52-week high

## Development

### Code Quality

The project uses pre-commit hooks for code quality:

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Testing

```bash
pytest tests/
```

### Documentation

```bash
# Build documentation (if using MkDocs)
mkdocs serve
```

## Technologies Used

- **Python 3.10+**: Core programming language
- **SQLite**: Database for data storage
- **pandas**: Data manipulation and analysis
- **yfinance**: Yahoo Finance API for market data
- **Flask**: Web framework (coming soon)
- **Chart.js/Plotly**: Data visualization (coming soon)

## Data Sources

- **Yahoo Finance**: Historical and current ETF price data
- **Manual Configuration**: ETF symbols and metadata

## License

This project is for educational and personal use.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

For issues and questions:
1. Check the [script execution guide](docs/how_to_run_scripts.md)
2. Review error logs for debugging information
3. Ensure all dependencies are properly installed

## Future Enhancements

- [ ] Web interface for data visualization
- [ ] Real-time price updates
- [ ] Additional technical indicators
- [ ] Portfolio tracking capabilities
- [ ] Email/SMS alerts for threshold breaches
- [ ] Support for more exchanges and asset types