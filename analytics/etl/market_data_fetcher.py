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
from typing import Optional, Dict, Any, List
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        logger.info(f"Fetching data for {ticker} from {start_date}")
        symbol = yf.Ticker(ticker)
        df = symbol.history(start=start_date)
        
        if df.empty:
            logger.warning(f"No data found for {ticker}")
            return None
            
        logger.info(f"Successfully fetched {len(df)} records for {ticker}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        return None

def get_active_symbols(db: DatabaseManager) -> List[Dict[str, Any]]:
    """
    Get all active symbols from the database.

    Args:
        db: Database manager instance

    Returns:
        List of dictionaries containing symbol information
    """
    try:
        symbols = db.get_active_symbols()
        logger.info(f"Found {len(symbols)} active symbols")
        return symbols
    except Exception as e:
        logger.error(f"Error getting active symbols: {e}")
        return []

def calculate_and_store_metrics(db: DatabaseManager, symbol_id: int, name: str) -> None:
    """
    Calculate and store metrics for a symbol using data from the database.

    Args:
        db: Database manager instance
        symbol_id: Symbol ID
        name: Symbol name for logging
    """
    try:
        today = datetime.now().date()
        year_ago = today - timedelta(days=365)
        
        # Get the data from database
        yearly_data = db.get_market_data_range(symbol_id, year_ago, today)
        if not yearly_data:
            logger.warning(f"No data found for {name} in the past year")
            return
            
        logger.info(f"Found {len(yearly_data)} days of data for {name}")
        
        # Calculate metrics
        high_52week = max(row['high'] for row in yearly_data)
        low_52week = min(row['low'] for row in yearly_data)
        
        # Find dates
        high_date = next(row['date'] for row in yearly_data if row['high'] == high_52week)
        low_date = next(row['date'] for row in yearly_data if row['low'] == low_52week)
        
        logger.info(f"Calculated metrics for {name}:")
        logger.info(f"52-week high: {high_52week:.2f} on {high_date}")
        logger.info(f"52-week low: {low_52week:.2f} on {low_date}")
        
        # Store metrics
        db.store_52week_metrics(
            symbol_id=symbol_id,
            calculation_date=today,
            high_52week=high_52week,
            low_52week=low_52week,
            high_date=high_date,
            low_date=low_date
        )
        
        logger.info(f"Successfully stored metrics for {name}")
        
    except Exception as e:
        logger.error(f"Error calculating metrics for {name}: {e}")
        raise

def main():
    """Main execution function for market data fetching."""
    logger.info("Starting market data fetch and metrics calculation")
    
    try:
        # Initialize database
        db = DatabaseManager()
        
        # Calculate start date (1 year ago from today)
        start_date = datetime.now() - timedelta(days=365)
        logger.info(f"Fetching data from {start_date}")
        
        # Get active symbols from database
        symbols = get_active_symbols(db)
        if not symbols:
            logger.error("No active symbols found in database")
            return
        
        for symbol in symbols:
            logger.info(f"Processing {symbol['name']} ({symbol['ticker']})")
            
            # Fetch data
            df = fetch_market_data(symbol['ticker'], start_date)
            if df is None:
                continue
                
            # Insert data into database
            try:
                db.insert_market_data(symbol['id'], df)
                logger.info(f"Successfully inserted market data for {symbol['name']}")
                
                # Calculate and store metrics
                calculate_and_store_metrics(db, symbol['id'], symbol['name'])
                
            except Exception as e:
                logger.error(f"Error processing data for {symbol['name']}: {e}")
                continue
        
        logger.info("Market data fetch and metrics calculation completed")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()