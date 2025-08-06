"""
Market Data Fetcher

This module fetches market data (prices, volumes) for configured symbols from Yahoo Finance.
It supports both ETFs and stocks, storing the data in a SQLite database for further analysis.
"""

import os
import sys
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from analytics.database.db_manager import DatabaseManager

def fetch_market_data(ticker: str, start_date: datetime) -> Optional[pd.DataFrame]:
    """
    Fetch market data from Yahoo Finance.

    Args:
        ticker: The Yahoo Finance ticker symbol
        start_date: Start date for data fetching

    Returns:
        DataFrame with OHLCV data or None if fetch fails
    """
    try:
        symbol = yf.Ticker(ticker)
        df = symbol.history(start=start_date)
        
        if df.empty:
            print(f"No data found for {ticker}")
            return None
            
        return df
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def get_active_symbols(db: DatabaseManager) -> Dict[str, Any]:
    """
    Get all active symbols from the database.

    Args:
        db: Database manager instance

    Returns:
        Dictionary of symbol information
    """
    return db.get_active_symbols()

def main():
    """Main execution function for market data fetching."""
    # Initialize database
    db = DatabaseManager()
    db.initialize_database()
    
    # Calculate start date (1 year ago from today)
    start_date = datetime.now() - timedelta(days=365)
    
    # Get active symbols from database
    symbols = get_active_symbols(db)
    
    for symbol in symbols:
        print(f"Fetching data for {symbol['name']} ({symbol['ticker']})")
        
        # Fetch data
        df = fetch_market_data(symbol['ticker'], start_date)
        if df is None:
            continue
            
        # Insert data into database
        try:
            db.insert_market_data(symbol['id'], df)
            print(f"Successfully inserted data for {symbol['name']}")
            
            # Update metrics
            today = datetime.now().date()
            db.update_52week_metrics(symbol['id'], today)
            print(f"Successfully updated metrics for {symbol['name']}")
            
        except Exception as e:
            print(f"Error processing data for {symbol['name']}: {e}")
            continue

if __name__ == "__main__":
    main()