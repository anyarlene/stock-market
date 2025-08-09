# Environment Setup Guide

This guide covers setting up the `market-env` virtual environment for both local and remote development.

## Virtual Environment Overview

The `market-env` environment is designed to:
- Isolate project dependencies
- Ensure consistent Python package versions
- Work seamlessly across different operating systems
- Support both local development and remote deployment

## Local Environment Setup

### Windows (Git Bash Recommended)

```bash
# Create the virtual environment
python -m venv market-env

# Activate the environment
source market-env/Scripts/activate

# Verify activation (should show market-env in prompt)
which python
# Should show: /path/to/stock-market/market-env/Scripts/python

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pandas, yfinance, sqlalchemy; print('Setup successful!')"
```

### Linux/Mac

```bash
# Create the virtual environment
python3 -m venv market-env

# Activate the environment
source market-env/bin/activate

# Verify activation
which python
# Should show: /path/to/stock-market/market-env/bin/python

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pandas, yfinance, sqlalchemy; print('Setup successful!')"
```

## Environment Management

### Activating the Environment

```bash
# Windows Git Bash
source market-env/Scripts/activate

# Linux/Mac
source market-env/bin/activate
```

### Deactivating the Environment

```bash
deactivate
```

### Checking Environment Status

```bash
# Check if environment is active
echo $VIRTUAL_ENV

# List installed packages
pip list

# Check Python version
python --version
```

## Dependency Management

### Core Dependencies

The project uses these essential packages:

- **pandas**: Data manipulation and analysis
- **yfinance**: Yahoo Finance API for market data
- **SQLAlchemy**: Database ORM and management
- **python-dotenv**: Environment variable management
- **matplotlib**: Data visualization
- **plotly**: Interactive charts

### Installing Additional Packages

```bash
# Activate environment first
source market-env/Scripts/activate  # Windows
# source market-env/bin/activate    # Linux/Mac

# Install new package
pip install package_name

# Update requirements.txt
pip freeze > requirements.txt
```

### Development Dependencies (Optional)

For development work, you can install additional tools:

```bash
# Install development tools
pip install pytest black isort flake8 mypy

# Or install from pyproject.toml
pip install -e ".[dev]"
```

## Remote Environment Setup

### SSH Access

For remote development, ensure SSH access is configured:

```bash
# Test SSH connection
ssh username@remote-server

# Clone repository on remote server
git clone <repository-url>
cd stock-market
```

### Remote Environment Creation

```bash
# Create environment on remote server
python3 -m venv market-env

# Activate environment
source market-env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Remote Development Workflow

```bash
# 1. Connect to remote server
ssh username@remote-server

# 2. Navigate to project
cd stock-market

# 3. Activate environment
source market-env/bin/activate

# 4. Run analytics scripts
python -m analytics.etl.market_data_fetcher

# 5. Export data for website
python -m analytics.etl.data_exporter
```

## Environment Variables

### Local Configuration

Create a `.env` file in the project root:

```env
# Database configuration
DATABASE_PATH=analytics/database/etf_database.db

# Environment settings
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO

# API settings (if needed)
YAHOO_FINANCE_TIMEOUT=30
```

### Remote Configuration

For remote environments, set environment variables:

```bash
# Set environment variables
export DATABASE_PATH=/path/to/analytics/database/etf_database.db
export DEBUG=False
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
```

## Troubleshooting

### Common Issues

1. **Environment Not Activating**
   ```bash
   # Check if environment exists
   ls -la market-env/
   
   # Recreate if corrupted
   rm -rf market-env
   python -m venv market-env
   ```

2. **Package Installation Errors**
   ```bash
   # Upgrade pip
   pip install --upgrade pip
   
   # Install with verbose output
   pip install -v -r requirements.txt
   ```

3. **Import Errors**
   ```bash
   # Verify environment is active
   echo $VIRTUAL_ENV
   
   # Check installed packages
   pip list | grep package_name
   ```

4. **Permission Issues (Linux/Mac)**
   ```bash
   # Fix permissions
   chmod +x market-env/bin/activate
   chmod +x market-env/bin/python
   ```

### Environment Verification

Run this script to verify your environment:

```bash
#!/bin/bash
echo "=== Environment Verification ==="

# Check if environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Virtual environment not active"
    exit 1
else
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
fi

# Check Python version
python --version

# Check core packages
python -c "
import pandas as pd
import yfinance as yf
import sqlalchemy as sa
print('✅ Core packages imported successfully')
"

# Check project structure
if [ -d "analytics" ] && [ -d "website" ]; then
    echo "✅ Project structure looks good"
else
    echo "❌ Project structure issues detected"
fi

echo "=== Verification Complete ==="
```

## Best Practices

1. **Always activate the environment** before running scripts
2. **Keep requirements.txt updated** when adding new packages
3. **Use .env files** for configuration, not hardcoded values
4. **Test in clean environment** before deploying changes
5. **Document environment-specific settings** in this guide

## Next Steps

- [Setup Guide](setup.md) - Complete project setup
- [Script Execution Guide](how_to_run_scripts.md) - Running analytics scripts
- [Project Overview](../README.md) - General project information
