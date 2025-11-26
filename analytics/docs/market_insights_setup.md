# ETF Insights Explorer - Local Testing Guide

This guide will help you set up and test the ETF Insights Explorer dashboard locally.

## Prerequisites

- Python 3.7+ installed
- Virtual environment activated (if using one)
- All base dependencies installed (`pip install -r requirements.txt`)

## Step-by-Step Setup

### Step 1: Install the Fear & Greed Index Package

The dashboard requires the `fear-greed-index` package to fetch market sentiment data.

```bash
pip install fear-greed-index
```

**Verify installation:**
```bash
python -c "from fear_greed_index.CNNFearAndGreedIndex import CNNFearAndGreedIndex; print('✅ Package installed successfully')"
```

### Step 2: Generate Market Insights Data

The dashboard needs JSON data files to display the visualizations. Generate them using the market insights fetcher:

```bash
python -m analytics.etl.market_insights_fetcher
```

**Expected output:**
```
📊 Starting market insights data export...
Fetching Fear & Greed Index...
✅ Successfully fetched Fear & Greed Index: XX (Classification)
Fetching S&P 500 sector data...
✅ Successfully fetched data for 11 sectors
Fetching holdings for VOO...
✅ Successfully fetched X holdings for VOO
...
✅ Market insights data export completed!
```

**Verify data files were created:**
```bash
# Check that these files exist in website/data/
ls website/data/fear_greed_index.json
ls website/data/sp500_sectors.json
ls website/data/etf_holdings.json
```

### Step 3: Start a Local Web Server

The dashboard needs to be served from a web server (not opened directly as a file) due to browser security restrictions for loading JSON files.

**Option A: Using Python's built-in HTTP server (Recommended)**

```bash
# Navigate to the website directory
cd website

# Python 3
python -m http.server 8000

# Or Python 2 (if needed)
python -m SimpleHTTPServer 8000
```

**Option B: Using Node.js http-server (if you have Node.js installed)**

```bash
# Install http-server globally (one time)
npm install -g http-server

# Navigate to website directory
cd website

# Start server
http-server -p 8000
```

### Step 4: Open the Dashboard in Your Browser

Once the server is running, open your web browser and navigate to:

```
http://localhost:8000/market-insights.html
```

You should see:
- **Fear & Greed Index** section with gauge and chart
- **S&P 500 Sector Performance** section with heatmap and cards
- **ETF Holdings Distribution** section with dropdown selector

### Step 5: Test Each Feature

#### Test Fear & Greed Index
- ✅ Check that the gauge shows a value (0-100)
- ✅ Verify the classification label (Extreme Fear, Fear, Neutral, Greed, Extreme Greed)
- ✅ Check that the historical chart displays a line graph

#### Test S&P 500 Sector Performance
- ✅ Verify the heatmap displays all 11 sectors
- ✅ Check that sector cards show change percentages
- ✅ Test the sort dropdown (Change % / Sector Name)

#### Test ETF Holdings
- ✅ Select an ETF from the dropdown (e.g., VOO, QQQ)
- ✅ Verify the pie chart displays top holdings
- ✅ Check that the holdings table shows company names and percentages

## Troubleshooting

### Issue: "Failed to fetch Fear & Greed Index" or "Data unavailable"

**Solution:**
1. Check internet connection
2. Verify the package is installed: `pip show fear-greed-index`
3. Try running the fetcher again: `python -m analytics.etl.market_insights_fetcher`
4. Check if CNN's website is accessible (the package scrapes from CNN)

### Issue: "Failed to fetch sector data" or empty sector list

**Solution:**
1. Check internet connection
2. Verify yfinance is working: `python -c "import yfinance as yf; print(yf.Ticker('SPY').info['shortName'])"`
3. Try running the fetcher again

### Issue: "No holdings data available for this ETF"

**Solution:**
1. Some ETFs may not have holdings data available via yfinance
2. Try a different ETF (VOO, QQQ usually work)
3. Check the console for error messages

### Issue: JSON files not loading (CORS errors)

**Solution:**
- Make sure you're using a web server (not opening the HTML file directly)
- Check that the server is running in the `website/` directory
- Verify the data files exist in `website/data/`

### Issue: Charts not displaying

**Solution:**
1. Open browser developer console (F12) and check for JavaScript errors
2. Verify Chart.js and Plotly are loading (check Network tab)
3. Check that data files are valid JSON (open them in a text editor)

## Quick Test Script

Run this to verify everything is set up correctly:

```bash
# 1. Check package installation
python -c "import fear_greed_index; print('✅ fear-greed-index installed')"

# 2. Generate data
python -m analytics.etl.market_insights_fetcher

# 3. Check data files exist
python -c "import os; files = ['website/data/fear_greed_index.json', 'website/data/sp500_sectors.json', 'website/data/etf_holdings.json']; [print(f'✅ {f} exists') if os.path.exists(f) else print(f'❌ {f} missing') for f in files]"

# 4. Start server (in website directory)
cd website && python -m http.server 8000
```

## Updating Data

To refresh the dashboard data:

1. Stop the web server (Ctrl+C)
2. Run the fetcher again: `python -m analytics.etl.market_insights_fetcher`
3. Refresh the browser page (F5)

## Integration with Full Workflow

The market insights export is automatically included in the full workflow:

```bash
# This will also generate market insights data
python analytics/enhanced_workflow.py --step full
```

Or run just the market insights export:

```bash
python analytics/enhanced_workflow.py --step insights
```

## Next Steps

Once testing is complete:
- Take a screenshot of the dashboard for the README
- Test on different browsers (Chrome, Firefox, Edge)
- Verify responsive design on mobile devices
- Check that all links between dashboards work correctly

