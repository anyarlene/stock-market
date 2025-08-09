"""
Enhanced Market Data Fetcher for Automation

This module provides enhanced market data fetching with:
- Incremental updates (only fetch new data)
- Data validation
- Error handling with retries
- UPSERT operations to avoid duplicates
- Comprehensive logging for automation
"""

import os
import sys
from datetime import datetime, timedelta, date
import yfinance as yf
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
import time
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Add the analytics directory to the Python path
analytics_path = Path(__file__).parent.parent
sys.path.append(str(analytics_path))

from database.db_manager import DatabaseManager

class EnhancedMarketDataFetcher:
    """Enhanced market data fetcher with incremental updates and validation."""
    
    def __init__(self, db_path: str = "database/etf_database.db"):
        """Initialize the enhanced fetcher."""
        self.db = DatabaseManager(db_path)
        self.max_retries = 3
        self.retry_delay = 60  # seconds
        
    def get_latest_data_date(self, symbol_id: int) -> Optional[date]:
        """Get the latest date for which we have data for a symbol."""
        try:
            self.db.connect()
            self.db.cursor.execute("""
                SELECT MAX(date) FROM etf_data WHERE symbol_id = ?
            """, (symbol_id,))
            
            result = self.db.cursor.fetchone()
            if result and result[0]:
                return datetime.strptime(result[0], '%Y-%m-%d').date()
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest data date for symbol {symbol_id}: {e}")
            return None
        finally:
            self.db.disconnect()
    
    def validate_data_quality(self, df: pd.DataFrame, symbol_name: str) -> Tuple[bool, List[str]]:
        """
        Validate data quality and return (is_valid, list_of_issues).
        
        Args:
            df: DataFrame with market data
            symbol_name: Symbol name for logging
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        if df.empty:
            issues.append("No data received")
            return False, issues
        
        # Check for missing values
        missing_counts = df.isnull().sum()
        for column, count in missing_counts.items():
            if count > 0:
                issues.append(f"Missing {count} values in {column}")
        
        # Check for negative prices
        price_columns = ['Open', 'High', 'Low', 'Close']
        for col in price_columns:
            if col in df.columns:
                negative_prices = (df[col] < 0).sum()
                if negative_prices > 0:
                    issues.append(f"Found {negative_prices} negative prices in {col}")
        
        # Check for extreme price movements (>50% in one day)
        if 'Close' in df.columns and len(df) > 1:
            price_changes = df['Close'].pct_change().abs()
            extreme_moves = (price_changes > 0.5).sum()
            if extreme_moves > 0:
                issues.append(f"Found {extreme_moves} extreme price movements (>50%)")
        
        # Check for reasonable volume
        if 'Volume' in df.columns:
            zero_volume = (df['Volume'] == 0).sum()
            if zero_volume > len(df) * 0.5:  # More than 50% zero volume
                issues.append(f"High number of zero volume days: {zero_volume}")
        
        is_valid = len(issues) == 0
        if not is_valid:
            logger.warning(f"Data quality issues for {symbol_name}: {issues}")
        else:
            logger.info(f"✅ Data quality validation passed for {symbol_name}")
        
        return is_valid, issues
    
    def fetch_market_data_with_retry(self, ticker: str, start_date: datetime, 
                                   symbol_name: str) -> Optional[pd.DataFrame]:
        """
        Fetch market data with retry logic and validation.
        
        Args:
            ticker: Yahoo Finance ticker
            start_date: Start date for fetching
            symbol_name: Symbol name for logging
            
        Returns:
            DataFrame with validated data or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching data for {symbol_name} ({ticker}) - Attempt {attempt + 1}/{self.max_retries}")
                logger.info(f"📅 Fetching from {start_date.strftime('%Y-%m-%d')} to present")
                
                symbol = yf.Ticker(ticker)
                df = symbol.history(start=start_date)
                
                if df.empty:
                    logger.warning(f"No data found for {symbol_name} ({ticker})")
                    return None
                
                # Validate data quality
                is_valid, issues = self.validate_data_quality(df, symbol_name)
                if not is_valid:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Data quality issues, retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        logger.error(f"Data quality validation failed after {self.max_retries} attempts")
                        return None
                
                # Log successful fetch
                first_date = df.index[0].strftime('%Y-%m-%d')
                last_date = df.index[-1].strftime('%Y-%m-%d')
                logger.info(f"✅ Successfully fetched {len(df)} records for {symbol_name}")
                logger.info(f"📅 Data range: {first_date} to {last_date}")
                
                return df
                
            except Exception as e:
                logger.error(f"Error fetching data for {symbol_name} ({ticker}) - Attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to fetch data for {symbol_name} after {self.max_retries} attempts")
                    return None
        
        return None
    
    def process_symbol_incremental(self, symbol: Dict[str, Any]) -> bool:
        """
        Process a single symbol with incremental updates.
        
        Args:
            symbol: Symbol dictionary with id, ticker, name, currency
            
        Returns:
            True if successful, False otherwise
        """
        symbol_id = symbol['id']
        ticker = symbol['ticker']
        name = symbol['name']
        currency = symbol['currency']
        
        logger.info(f"\n📊 Processing {name} ({ticker}) - Incremental Update")
        
        try:
            # Get the latest date we have data for
            latest_date = self.get_latest_data_date(symbol_id)
            
            if latest_date:
                # Incremental update: fetch from day after latest date
                start_date = latest_date + timedelta(days=1)
                logger.info(f"🔄 Incremental update: fetching from {start_date.strftime('%Y-%m-%d')}")
                
                # Check if we need to fetch (avoid fetching if latest date is today)
                today = datetime.now().date()
                if start_date > today:
                    logger.info(f"✅ {name} is already up to date (latest: {latest_date})")
                    return True
            else:
                # Full fetch: start from December 1, 2021
                start_date = datetime(2021, 12, 1)
                logger.info(f"🆕 Full fetch: fetching from {start_date.strftime('%Y-%m-%d')}")
            
            # Fetch data with retry logic
            df = self.fetch_market_data_with_retry(ticker, start_date, name)
            if df is None:
                logger.error(f"❌ Failed to fetch data for {name}")
                return False
            
            # Insert data using UPSERT (INSERT OR REPLACE)
            self.db.insert_market_data(symbol_id, df, currency=currency)
            logger.info(f"✅ Successfully inserted {len(df)} records for {name}")
            
            # Calculate and store metrics
            self.calculate_and_store_metrics(symbol_id, name)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing {name}: {e}")
            return False
    
    def calculate_and_store_metrics(self, symbol_id: int, name: str) -> None:
        """Calculate and store 52-week metrics for a symbol."""
        try:
            today = datetime.now().date()
            year_ago = today - timedelta(days=365)
            
            # Get the data from database
            yearly_data = self.db.get_market_data_range(symbol_id, year_ago, today)
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
            
            logger.info(f"📊 Calculated metrics for {name}:")
            logger.info(f"   52-week high: {high_52week:.2f} on {high_date}")
            logger.info(f"   52-week low: {low_52week:.2f} on {low_date}")
            
            # Store metrics
            self.db.store_52week_metrics(
                symbol_id=symbol_id,
                calculation_date=today,
                high_52week=high_52week,
                low_52week=low_52week,
                high_date=high_date,
                low_date=low_date
            )
            
            logger.info(f"✅ Successfully stored metrics for {name}")
            
        except Exception as e:
            logger.error(f"❌ Error calculating metrics for {name}: {e}")
            raise
    
    def run_incremental_update(self) -> Dict[str, Any]:
        """
        Run incremental update for all active symbols.
        
        Returns:
            Dictionary with results summary
        """
        logger.info("🚀 Starting Enhanced Market Data Fetcher - Incremental Update")
        logger.info(f"📅 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'total_symbols': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Get active symbols
            symbols = self.db.get_active_symbols()
            if not symbols:
                logger.error("❌ No active symbols found in database")
                results['errors'].append("No active symbols found")
                return results
            
            results['total_symbols'] = len(symbols)
            logger.info(f"📊 Found {len(symbols)} active symbols")
            
            # Process each symbol
            for symbol in symbols:
                success = self.process_symbol_incremental(symbol)
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to process {symbol['name']} ({symbol['ticker']})")
            
            # Log summary
            logger.info(f"\n🎉 Incremental Update Completed")
            logger.info(f"📊 Summary:")
            logger.info(f"   Total symbols: {results['total_symbols']}")
            logger.info(f"   Successful: {results['successful']}")
            logger.info(f"   Failed: {results['failed']}")
            
            if results['failed'] > 0:
                logger.warning(f"⚠️  {results['failed']} symbols failed to update")
                for error in results['errors']:
                    logger.error(f"   ❌ {error}")
            
            results['end_time'] = datetime.now().isoformat()
            results['duration'] = (datetime.now() - datetime.fromisoformat(results['start_time'])).total_seconds()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Critical error in incremental update: {e}")
            results['errors'].append(f"Critical error: {str(e)}")
            results['end_time'] = datetime.now().isoformat()
            return results

def main():
    """Main execution function for enhanced market data fetching."""
    fetcher = EnhancedMarketDataFetcher()
    results = fetcher.run_incremental_update()
    
    # Save results to file for monitoring
    results_file = "analytics/logs/update_results.json"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📄 Results saved to {results_file}")
    
    # Exit with error code if any failures
    if results['failed'] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
