# ETF Analytics and Visualization

This project provides ETF analytics and visualization through a web interface. It tracks ETF prices, calculates 52-week metrics, and visualizes price movements with various decrease thresholds.

## Project Structure

```
stock-market/
├── analytics/                  # Analytics package
│   ├── __init__.py
│   ├── database/              # Database management
│   │   ├── __init__.py
│   │   ├── db_manager.py      # Database operations
│   │   └── schema.sql         # Database schema
│   ├── etl/                   # ETL processes
│   │   ├── __init__.py
│   │   └── update_etf_data.py # Data pipeline script
│   ├── models/                # Analytics models
│   │   ├── __init__.py
│   │   └── metrics.py         # ETF metrics calculations
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       └── helpers.py
├── website/                   # Website package
│   ├── __init__.py
│   ├── static/               # Static files
│   │   ├── css/
│   │   └── js/
│   ├── templates/            # HTML templates
│   └── app.py               # Website application
├── data/                     # Data storage
│   └── etf_database.db      # SQLite database
├── tests/                    # Test files
│   ├── __init__.py
│   └── unit/
│       ├── __init__.py
│       ├── test_db_manager.py
│       └── test_metrics.py
├── .github/                  # GitHub specific files
│   └── workflows/            # GitHub Actions
│       └── update_etf_data.yml
├── .gitignore
├── requirements.txt          # Project dependencies
└── README.md                # Project documentation
```

## Components

### Analytics Package
- Database management (SQLite)
- ETL processes for data ingestion
- ETF metrics calculations
- Helper utilities

### Website Package
- Web interface for ETF visualization
- Interactive charts
- 52-week metrics display
- Decrease thresholds visualization

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```bash
   python -m analytics.database.db_manager
   ```
4. Run the website:
   ```bash
   python -m website.app
   ```

## Data Updates

Data is automatically updated daily after market close using GitHub Actions. You can also manually trigger updates through the GitHub Actions interface or run locally:
```bash
python -m analytics.etl.update_etf_data
```

## Development

### Running Tests
```bash
pytest tests/
```

### Local Development
1. Set up a virtual environment
2. Install development dependencies
3. Run the local development server