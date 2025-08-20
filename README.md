# ETF Analytics Dashboard

A comprehensive ETF analytics platform with real-time market data, currency conversion, and interactive visualizations for European market analysis.

## 🚀 Features

- **Real-time Market Data**: Historical price data from 2021-12-01 onwards
- **Multi-Currency Support**: Automatic USD/GBP to EUR conversion with historical rates
- **Interactive Charts**: Time range filtering, currency toggling, and metric selection
- **Profit Target Analysis**: Entry point identification and profit target calculations
- **Responsive Design**: Modern UI with mobile-friendly interface

## 📊 Supported ETFs

- **Vanguard S&P 500 UCITS ETF (VUAA.L)** - USD denominated
- **iShares NASDAQ 100 UCITS ETF (CNDX.L)** - GBP denominated

## 🏗️ Architecture

### ETL Pipeline
The system uses a **modular ETL workflow**:

```
📊 Database Init → 📋 Load Symbols → 📈 Fetch Data → 💱 Convert Currencies → 📤 Export Data
```

### Key Components
- **SQLite Database**: Efficient local storage with proper indexing
- **Currency Conversion**: Historical rate caching for performance
- **Batch Processing**: Optimized for large datasets
- **Modular Testing**: Individual step testing and debugging

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Git

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd stock-market

# Create virtual environment
python -m venv market-env
source market-env/bin/activate  # On Windows: market-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Run Complete ETL Workflow
```bash
# From stock-market/ directory
python analytics/enhanced_workflow.py --step full
```

This single command runs the entire pipeline:
- Initializes database with complete schema
- Loads ETF symbols
- Fetches market data from 2021-12-01
- Converts currencies to EUR using historical rates
- Exports data for the website

### 2. Test Individual Steps
```bash
# Test only incremental update
python analytics/enhanced_workflow.py --step incremental

# Test only currency conversion
python analytics/enhanced_workflow.py --step currency

# Test only data export
python analytics/enhanced_workflow.py --step export
```

### 3. Open Website
Open `website/index.html` in your browser to view the dashboard.

## 🤖 Automation Setup

The system includes automated daily updates via GitHub Actions with separate testing and production environments:

### **Workflow Structure**

**Testing Environment (`automation-daily-update` branch):**
- `test_daily_update.yml` - Runs when you push to test branch (for testing daily workflow)

**Production Environment (`main` branch):**
- `production_automation.yml` - Runs daily at 10 PM Berlin time (production automation)

### **Automatic Daily Updates**
- **Schedule**: Daily at 10 PM Berlin time (UTC+1)
- **Process**: Incremental data fetch → Currency conversion → Database update
- **Monitoring**: Real-time logs in GitHub Actions
- **Zero Maintenance**: Fully automated, no manual intervention required

### **Setup Automation**
1. **Test on your branch**: Push to `automation-daily-update` to test workflows
2. **Deploy to production**: Merge to `main` branch for production automation
3. **Monitor**: Check GitHub Actions tab for workflow status

### **Monitoring**
- **GitHub Actions**: Repository → Actions tab
- **Workflow Logs**: Check `analytics/logs/workflow_results.json` for detailed results
- **Database Updates**: Committed automatically to repository

## 📁 Project Structure

```
stock-market/
├── analytics/                    # ETL Pipeline
│   ├── enhanced_workflow.py     # Main orchestrator
│   ├── database_diagnostic.py   # Debugging tool
│   ├── database/
│   │   ├── db_manager.py        # Database operations
│   │   ├── schema.sql           # Complete database schema
│   │   └── load_symbols.py      # Load ETF symbols
│   ├── etl/
│   │   ├── market_data_fetcher.py    # Fetch market data
│   │   ├── enhanced_market_data_fetcher.py # Enhanced data fetcher
│   │   ├── currency_converter_etl.py # Convert currencies
│   │   └── data_exporter.py          # Export for website
│   ├── utils/
│   │   └── currency_converter.py     # Currency conversion logic
│   └── logs/                    # Automation logs
├── .github/workflows/           # GitHub Actions
│   ├── test_daily_update.yml    # Testing workflow
│   └── production_automation.yml # Production workflow
├── website/                     # Frontend Dashboard
│   ├── index.html              # Main dashboard
│   ├── css/style.css           # Styling
│   ├── js/app.js               # Interactive features
│   └── data/                   # Exported JSON data
└── requirements.txt            # Python dependencies
```

## 💱 Currency Conversion

The system automatically converts USD and GBP prices to EUR using:

- **Historical Exchange Rates**: Fetched from Yahoo Finance
- **Rate Caching**: Stored in database for performance
- **Batch Processing**: Efficient conversion of large datasets
- **Fallback Handling**: Graceful error handling for missing rates

## 🔧 Configuration

### Database
- **Location**: `analytics/database/etf_database.db`
- **Schema**: Automatically created from `schema.sql`
- **Backup**: Database file can be backed up for data preservation

### Data Sources
- **Market Data**: Yahoo Finance via `yfinance`
- **Exchange Rates**: Yahoo Finance currency pairs
- **Historical Period**: 2021-12-01 to present

## 🧪 Testing & Debugging

### Database Diagnostics
```bash
python analytics/database_diagnostic.py
```

### Individual Component Testing
```bash
# Test currency conversion
python analytics/etl/currency_converter_etl.py

# Test data export
python analytics/etl/data_exporter.py

# Test market data fetching
python analytics/etl/market_data_fetcher.py
```

## 📈 Performance Features

- **Batch Currency Conversion**: Reduces API calls by 75%
- **Database Indexing**: Optimized queries for large datasets
- **Rate Caching**: Avoids repeated exchange rate fetches
- **Modular Processing**: Parallel development and testing

## 🔄 Workflow Steps

1. **Database Initialization**: Creates all tables and indices
2. **Symbol Loading**: Loads ETF definitions and metadata
3. **Market Data Fetching**: Retrieves historical price data
4. **Currency Conversion**: Converts prices to EUR using historical rates
5. **Data Export**: Generates JSON files for website consumption

## 🛡️ Error Handling

- **Graceful Failures**: Individual step failures don't break the pipeline
- **Comprehensive Logging**: Detailed error messages and progress tracking
- **Data Validation**: Ensures data integrity throughout the process
- **Fallback Mechanisms**: Handles missing data and API failures

## 📝 Development

### Adding New ETFs
1. Update `analytics/database/load_symbols.py`
2. Run `python analytics/workflow.py --step fetch`
3. Test with `python analytics/workflow.py --step currency`

### Extending Features
- **New Metrics**: Add to `analytics/etl/market_data_fetcher.py`
- **Additional Currencies**: Extend `analytics/utils/currency_converter.py`
- **UI Enhancements**: Modify `website/js/app.js`

