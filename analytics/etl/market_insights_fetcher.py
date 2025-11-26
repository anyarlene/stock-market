#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Insights Data Fetcher
Fetches data for the ETF Insights Explorer dashboard:
- Fear & Greed Index
- S&P 500 sector data
- ETF holdings data
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add the analytics directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import pandas as pd
import requests

# Try to import fear-greed-index, but handle if not installed
# Package name: fear-greed-index, import: fear_greed_index
FEAR_GREED_AVAILABLE = False
FearGreedIndex = None

try:
    from fear_greed_index.CNNFearAndGreedIndex import CNNFearAndGreedIndex
    FearGreedIndex = CNNFearAndGreedIndex
    FEAR_GREED_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import
        from fear_greed_index import FearGreedIndex
        FEAR_GREED_AVAILABLE = True
    except ImportError:
        FEAR_GREED_AVAILABLE = False
        logging.warning("fear-greed-index package not installed. Install with: pip install fear-greed-index")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_fear_greed_index() -> Optional[Dict[str, Any]]:
    """
    Fetch Fear & Greed Index data.
    Uses alternative API if the fear-greed-index package fails.
    
    Returns:
        Dictionary with index data or None if failed
    """
    # Try using the fear-greed-index package first
    if FEAR_GREED_AVAILABLE and FearGreedIndex is not None:
        try:
            logger.info("Fetching Fear & Greed Index using fear-greed-index package...")
            fgi = FearGreedIndex()
            current = fgi.get()
            historical = fgi.get_historical(days=30)
            
            # Format current data
            current_data = {
                "value": current.value if hasattr(current, 'value') else int(current),
                "classification": current.classification if hasattr(current, 'classification') else str(current),
                "timestamp": current.timestamp.isoformat() if hasattr(current, 'timestamp') and hasattr(current.timestamp, 'isoformat') else str(current.timestamp) if hasattr(current, 'timestamp') else datetime.now().isoformat()
            }
            
            # Format historical data
            historical_data = []
            for item in historical:
                historical_data.append({
                    "value": item.value if hasattr(item, 'value') else int(item),
                    "classification": item.classification if hasattr(item, 'classification') else str(item),
                    "timestamp": item.timestamp.isoformat() if hasattr(item, 'timestamp') and hasattr(item.timestamp, 'isoformat') else str(item.timestamp) if hasattr(item, 'timestamp') else datetime.now().isoformat()
                })
            
            data = {
                "current": current_data,
                "historical": historical_data,
                "lastUpdated": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Successfully fetched Fear & Greed Index: {current_data['value']} ({current_data['classification']})")
            return data
        except Exception as e:
            logger.warning(f"fear-greed-index package failed: {e}. Trying alternative method...")
    
    # Fallback: Use alternative API (Alternative.me Fear & Greed Index API)
    try:
        logger.info("Fetching Fear & Greed Index using alternative API...")
        import requests
        
        # Alternative.me Fear & Greed Index API (free, no API key required)
        api_url = "https://api.alternative.me/fng/?limit=30"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        api_data = response.json()
        
        if api_data.get('data') and len(api_data['data']) > 0:
            # Get current (most recent)
            current_item = api_data['data'][0]
            current_value = int(current_item['value'])
            
            # Log the raw API response for debugging
            logger.debug(f"API returned value: {current_value}, timestamp: {current_item.get('timestamp')}")
            
            # Map value to classification
            if current_value <= 25:
                classification = "Extreme Fear"
            elif current_value <= 45:
                classification = "Fear"
            elif current_value <= 55:
                classification = "Neutral"
            elif current_value <= 75:
                classification = "Greed"
            else:
                classification = "Extreme Greed"
            
            current_data = {
                "value": current_value,
                "classification": classification,
                "timestamp": datetime.fromtimestamp(int(current_item['timestamp'])).isoformat()
            }
            
            # Format historical data
            historical_data = []
            for item in api_data['data']:
                value = int(item['value'])
                if value <= 25:
                    item_classification = "Extreme Fear"
                elif value <= 45:
                    item_classification = "Fear"
                elif value <= 55:
                    item_classification = "Neutral"
                elif value <= 75:
                    item_classification = "Greed"
                else:
                    item_classification = "Extreme Greed"
                
                historical_data.append({
                    "value": value,
                    "classification": item_classification,
                    "timestamp": datetime.fromtimestamp(int(item['timestamp'])).isoformat()
                })
            
            data = {
                "current": current_data,
                "historical": historical_data,
                "lastUpdated": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Successfully fetched Fear & Greed Index: {current_value} ({classification})")
            return data
    except Exception as e:
        logger.error(f"Error fetching Fear & Greed Index from alternative API: {e}")
    
    logger.error("All Fear & Greed Index fetch methods failed")
    return None


def fetch_sp500_sector_data() -> Optional[Dict[str, Any]]:
    """
    Fetch S&P 500 sector performance data including individual companies.
    
    Returns:
        Dictionary with sector and company data or None if failed
    """
    try:
        logger.info("Fetching S&P 500 sector and company data...")
        
        # Get S&P 500 ETF (SPY) to get top holdings
        spy = yf.Ticker("SPY")
        spy_info = spy.info
        
        # Get sector ETFs for S&P 500 sectors
        sector_etfs = {
            "Technology": "XLK",
            "Healthcare": "XLV",
            "Financials": "XLF",
            "Consumer Discretionary": "XLY",
            "Communication Services": "XLC",
            "Industrials": "XLI",
            "Consumer Staples": "XLP",
            "Energy": "XLE",
            "Utilities": "XLU",
            "Real Estate": "XLRE",
            "Materials": "XLB"
        }
        
        sector_data = []
        company_data = []
        
        # Fetch sector data
        for sector_name, ticker in sector_etfs.items():
            try:
                sector_ticker = yf.Ticker(ticker)
                info = sector_ticker.info
                hist = sector_ticker.history(period="1mo")
                
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    previous_price = float(hist['Close'].iloc[0])
                    change_pct = ((current_price - previous_price) / previous_price) * 100
                    
                    sector_data.append({
                        "sector": sector_name,
                        "ticker": ticker,
                        "currentPrice": round(current_price, 2),
                        "changePercent": round(change_pct, 2),
                        "marketCap": info.get("marketCap", 0)
                    })
                    
            except Exception as e:
                logger.warning(f"Error fetching data for {sector_name} ({ticker}): {e}")
                continue
        
        # Fetch top S&P 500 companies (using SPY top holdings as proxy)
        # Get major companies from each sector
        top_companies = [
            # Technology
            {"symbol": "AAPL", "name": "Apple Inc", "sector": "Technology"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
            {"symbol": "GOOGL", "name": "Alphabet Inc", "sector": "Technology"},
            {"symbol": "META", "name": "Meta Platforms Inc", "sector": "Technology"},
            # Healthcare
            {"symbol": "UNH", "name": "UnitedHealth Group", "sector": "Healthcare"},
            {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
            {"symbol": "LLY", "name": "Eli Lilly and Company", "sector": "Healthcare"},
            {"symbol": "ABBV", "name": "AbbVie Inc", "sector": "Healthcare"},
            # Financials
            {"symbol": "JPM", "name": "JPMorgan Chase & Co", "sector": "Financials"},
            {"symbol": "BAC", "name": "Bank of America Corp", "sector": "Financials"},
            {"symbol": "WFC", "name": "Wells Fargo & Company", "sector": "Financials"},
            # Consumer Discretionary
            {"symbol": "AMZN", "name": "Amazon.com Inc", "sector": "Consumer Discretionary"},
            {"symbol": "TSLA", "name": "Tesla Inc", "sector": "Consumer Discretionary"},
            {"symbol": "HD", "name": "The Home Depot Inc", "sector": "Consumer Discretionary"},
            # Energy
            {"symbol": "XOM", "name": "Exxon Mobil Corporation", "sector": "Energy"},
            {"symbol": "CVX", "name": "Chevron Corporation", "sector": "Energy"},
            # Industrials
            {"symbol": "BA", "name": "The Boeing Company", "sector": "Industrials"},
            {"symbol": "CAT", "name": "Caterpillar Inc", "sector": "Industrials"},
            # Consumer Staples
            {"symbol": "WMT", "name": "Walmart Inc", "sector": "Consumer Staples"},
            {"symbol": "PG", "name": "Procter & Gamble Co", "sector": "Consumer Staples"},
        ]
        
        for company in top_companies:
            try:
                ticker = yf.Ticker(company["symbol"])
                info = ticker.info
                hist = ticker.history(period="1mo")
                
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    previous_price = float(hist['Close'].iloc[0])
                    change_pct = ((current_price - previous_price) / previous_price) * 100
                    market_cap = info.get("marketCap", 0)
                    
                    # Calculate weight based on market cap (simplified)
                    weight = (market_cap / 1e12) * 100 if market_cap > 0 else 0
                    
                    company_data.append({
                        "symbol": company["symbol"],
                        "name": company["name"],
                        "sector": company["sector"],
                        "currentPrice": round(current_price, 2),
                        "changePercent": round(change_pct, 2),
                        "marketCap": market_cap,
                        "weight": round(weight, 2)
                    })
                    
            except Exception as e:
                logger.debug(f"Error fetching data for {company['symbol']}: {e}")
                continue
        
        # Sort sectors by change percentage
        sector_data.sort(key=lambda x: x["changePercent"], reverse=True)
        
        # Sort companies by weight (market cap)
        company_data.sort(key=lambda x: x["weight"], reverse=True)
        
        result = {
            "sectors": sector_data,
            "companies": company_data,
            "lastUpdated": datetime.now().isoformat(),
            "totalSectors": len(sector_data),
            "totalCompanies": len(company_data)
        }
        
        logger.info(f"✅ Successfully fetched data for {len(sector_data)} sectors and {len(company_data)} companies")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching S&P 500 sector data: {e}")
        return None


def fetch_etf_holdings(etf_ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch ETF holdings data using yfinance.
    Tries multiple methods to get holdings data.
    
    Args:
        etf_ticker: ETF ticker symbol (e.g., "VOO", "QQQ")
        
    Returns:
        Dictionary with holdings data or None if failed
    """
    try:
        logger.info(f"Fetching holdings for {etf_ticker}...")
        
        ticker = yf.Ticker(etf_ticker)
        info = ticker.info
        
        holdings_data = {
            "ticker": etf_ticker,
            "name": info.get("longName", info.get("shortName", etf_ticker)),
            "holdings": [],
            "totalHoldings": info.get("holdingsCount", 0),
            "lastUpdated": datetime.now().isoformat()
        }
        
        # Method 1: Try to get top holdings from info dict
        top_holdings = info.get("topHoldings", [])
        if top_holdings:
            for holding in top_holdings:
                if isinstance(holding, dict):
                    name = holding.get("name", holding.get("symbol", "Unknown"))
                    pct = holding.get("percent", holding.get("percentage", 0))
                    if pct > 0:
                        holdings_data["holdings"].append({
                            "name": name,
                            "percentage": round(float(pct), 2)
                        })
        
        # Method 2: Try institutional_holders (these are often the top holdings)
        if not holdings_data["holdings"]:
            try:
                institutional_holders = ticker.institutional_holders
                if institutional_holders is not None and not institutional_holders.empty:
                    # institutional_holders has columns: Holder, Shares, Date Reported, % Out, Value
                    for idx, row in institutional_holders.iterrows():
                        try:
                            holder_name = str(row.iloc[0]) if len(row) > 0 else "Unknown"
                            pct_out = float(row.iloc[3]) if len(row) > 3 else 0
                            if pct_out > 0:
                                holdings_data["holdings"].append({
                                    "name": holder_name,
                                    "percentage": round(pct_out * 100, 2)  # Convert to percentage
                                })
                        except (ValueError, IndexError) as e:
                            logger.debug(f"Error parsing institutional holder: {e}")
                            continue
            except Exception as e:
                logger.debug(f"Institutional holders method failed: {e}")
        
        # Method 3: Try major_holders as fallback
        if not holdings_data["holdings"]:
            try:
                major_holders = ticker.major_holders
                if major_holders is not None and not major_holders.empty:
                    for idx, row in major_holders.iterrows():
                        if len(row) >= 2:
                            try:
                                pct_str = str(row.iloc[0]).replace('%', '').strip()
                                percentage = float(pct_str)
                                holder_name = str(row.iloc[1]).strip()
                                
                                holdings_data["holdings"].append({
                                    "name": holder_name,
                                    "percentage": round(percentage, 2)
                                })
                            except (ValueError, IndexError) as e:
                                logger.debug(f"Error parsing major holder: {e}")
                                continue
            except Exception as e:
                logger.debug(f"Major holders method failed: {e}")
        
        # If we have holdings, sort by percentage (descending)
        if holdings_data["holdings"]:
            holdings_data["holdings"].sort(key=lambda x: x["percentage"], reverse=True)
            # Limit to top 10 for display
            holdings_data["holdings"] = holdings_data["holdings"][:10]
            logger.info(f"✅ Successfully fetched {len(holdings_data['holdings'])} holdings for {etf_ticker}")
        else:
            logger.warning(f"No holdings data found for {etf_ticker} using any method")
        
        return holdings_data
        
    except Exception as e:
        logger.error(f"Error fetching holdings for {etf_ticker}: {e}")
        return None


def export_market_insights_data(output_dir: str = "website/data") -> None:
    """
    Export all market insights data to JSON files.
    
    Args:
        output_dir: Directory to save JSON files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("📊 Starting market insights data export...")
    
    # Fetch Fear & Greed Index
    fear_greed_data = fetch_fear_greed_index()
    if fear_greed_data:
        fear_greed_file = os.path.join(output_dir, "fear_greed_index.json")
        with open(fear_greed_file, 'w', encoding='utf-8') as f:
            json.dump(fear_greed_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Exported Fear & Greed Index to {fear_greed_file}")
    else:
        logger.warning("⚠️  Could not fetch Fear & Greed Index data")
    
    # Fetch S&P 500 sector data
    sector_data = fetch_sp500_sector_data()
    if sector_data:
        sector_file = os.path.join(output_dir, "sp500_sectors.json")
        with open(sector_file, 'w', encoding='utf-8') as f:
            json.dump(sector_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Exported S&P 500 sector data to {sector_file}")
    else:
        logger.warning("⚠️  Could not fetch S&P 500 sector data")
    
    # Fetch ETF holdings for common ETFs
    etf_tickers = ["VOO", "QQQ", "VTI", "VUAA.L", "CNDX.L"]
    etf_holdings = {}
    
    for ticker in etf_tickers:
        holdings = fetch_etf_holdings(ticker)
        if holdings:
            etf_holdings[ticker] = holdings
    
    if etf_holdings:
        holdings_file = os.path.join(output_dir, "etf_holdings.json")
        with open(holdings_file, 'w', encoding='utf-8') as f:
            json.dump(etf_holdings, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Exported ETF holdings for {len(etf_holdings)} ETFs to {holdings_file}")
    else:
        logger.warning("⚠️  Could not fetch ETF holdings data")
    
    logger.info("✅ Market insights data export completed!")


def main():
    """Main function to export market insights data."""
    export_market_insights_data()


if __name__ == "__main__":
    main()

