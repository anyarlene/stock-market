# Stock Market Analytics

A comprehensive tool for ETF analytics and visualization. Track ETF prices, calculate 52-week metrics, and visualize price movements with decrease thresholds.

## Project Overview

This project consists of two main components:

- **Analytics**: Core data processing and analysis engine
- **Website**: Interactive web dashboard for data visualization

## Features

- **ETF Price Tracking**: Daily price updates for configured ETFs
- **52-Week Metrics**: Track high/low points and important dates
- **Decrease Thresholds**: Monitor 10%, 15%, 20%, 25%, and 30% decreases from 52-week high
- **Interactive Web Dashboard**: Chart.js visualization with ETF switching and threshold monitoring

## Quick Start

See [docs/setup.md](docs/setup.md) for detailed setup instructions.

## Project Structure

```
stock-market/
├── analytics/                  # Core analytics package
│   ├── database/              # Database management
│   ├── etl/                   # ETL processes
│   ├── models/                # Analytics models
│   ├── utils/                 # Utility functions
│   └── docs/                  # Documentation
├── website/                   # Web dashboard
│   ├── index.html             # Main dashboard page
│   ├── css/                   # Dashboard styling
│   ├── js/                    # Chart.js visualization
│   └── data/                  # Generated data files
```

## Current ETFs

The system currently tracks:
- **Vanguard S&P 500 UCITS ETF** (VUAA.L)
- **iShares NASDAQ 100 UCITS ETF** (CNDX.L)

## Documentation

- [Setup Guide](analytics/docs/setup.md) - How to set up and run the project
- [Script Execution](analytics/docs/how_to_run_scripts.md) - How to run individual scripts
- [Environment Setup](analytics/docs/environment-setup.md) - Virtual environment configuration

## Technologies Used

- **Python 3.10+**: Core programming language
- **SQLite**: Database for data storage
- **pandas**: Data manipulation and analysis
- **yfinance**: Yahoo Finance API for market data
- **Chart.js**: Data visualization

## License

This project is for educational and personal use.