#!/usr/bin/env python3
"""
Currency Converter Utility

This module handles currency conversions for ETF data, specifically converting
USD and GBP prices to EUR for European market analysis.
"""

import yfinance as yf
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
import logging
import sqlite3
import os

logger = logging.getLogger(__name__)

class CurrencyConverter:
    """Handles currency conversions for ETF data with historical rate support."""
    
    def __init__(self, db_path: str = "database/etf_database.db"):
        self.db_path = db_path
        self.exchange_rates = {}
        self.last_update = None
    
    def get_historical_exchange_rates(self, from_currency: str, start_date: date, end_date: date, 
                                    to_currency: str = 'EUR') -> Dict[str, float]:
        """
        Get historical exchange rates for a date range.
        
        Args:
            from_currency: Source currency (USD, GBP, etc.)
            to_currency: Target currency (default: EUR)
            start_date: Start date for rate fetching
            end_date: End date for rate fetching
            
        Returns:
            Dictionary mapping date strings to exchange rates
        """
        if from_currency == to_currency:
            # Return 1.0 for all dates if same currency
            rates = {}
            current_date = start_date
            while current_date <= end_date:
                rates[current_date.strftime('%Y-%m-%d')] = 1.0
                current_date += timedelta(days=1)
            return rates
        
        try:
            # Use yfinance for historical rates
            if from_currency == 'USD' and to_currency == 'EUR':
                symbol = 'USDEUR=X'
            elif from_currency == 'GBP' and to_currency == 'EUR':
                symbol = 'GBPEUR=X'
            else:
                logger.warning(f"Unsupported currency pair: {from_currency}/{to_currency}")
                return {}
            
            logger.info(f"Fetching historical rates for {from_currency}/{to_currency} from {start_date} to {end_date}")
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date + timedelta(days=1))
            
            if hist.empty:
                logger.error(f"No historical data found for {symbol}")
                return {}
            
            rates = {}
            for date_str, row in hist.iterrows():
                date_key = date_str.strftime('%Y-%m-%d')
                rates[date_key] = float(row['Close'])
            
            logger.info(f"Fetched {len(rates)} exchange rates for {from_currency}/{to_currency}")
            return rates
            
        except Exception as e:
            logger.error(f"Error fetching historical rates for {from_currency}/{to_currency}: {e}")
            return {}
    
    def store_exchange_rates(self, from_currency: str, to_currency: str, rates: Dict[str, float]):
        """
        Store exchange rates in the database.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            rates: Dictionary mapping date strings to rates
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for date_str, rate in rates.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO currency_rates 
                    (from_currency, to_currency, rate_date, exchange_rate)
                    VALUES (?, ?, ?, ?)
                """, (from_currency, to_currency, date_str, rate))
            
            conn.commit()
            logger.info(f"Stored {len(rates)} exchange rates for {from_currency}/{to_currency}")
            
        except sqlite3.Error as e:
            logger.error(f"Error storing exchange rates: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_cached_exchange_rate(self, from_currency: str, to_currency: str, target_date: date) -> Optional[float]:
        """
        Get exchange rate from database cache.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            target_date: Target date for rate
            
        Returns:
            Exchange rate or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT exchange_rate FROM currency_rates 
                WHERE from_currency = ? AND to_currency = ? AND rate_date = ?
            """, (from_currency, to_currency, target_date.strftime('%Y-%m-%d')))
            
            row = cursor.fetchone()
            return float(row[0]) if row else None
            
        except sqlite3.Error as e:
            logger.error(f"Error getting cached exchange rate: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_exchange_rate(self, from_currency: str, to_currency: str = 'EUR', 
                         target_date: Optional[date] = None) -> Optional[float]:
        """
        Get exchange rate for currency conversion.
        
        Args:
            from_currency: Source currency (USD, GBP, etc.)
            to_currency: Target currency (default: EUR)
            target_date: Specific date for historical rates (optional)
            
        Returns:
            Exchange rate or None if not available
        """
        if from_currency == to_currency:
            return 1.0
        
        # Use current date if no target date provided
        if target_date is None:
            target_date = date.today()
        
        # Try to get from cache first
        cached_rate = self.get_cached_exchange_rate(from_currency, to_currency, target_date)
        if cached_rate is not None:
            return cached_rate
        
        # If not in cache, fetch and store
        rates = self.get_historical_exchange_rates(from_currency, to_currency, target_date, target_date)
        if rates:
            self.store_exchange_rates(from_currency, to_currency, rates)
            return rates.get(target_date.strftime('%Y-%m-%d'))
        
        return None
    
    def convert_price(self, price: float, from_currency: str, to_currency: str = 'EUR',
                     target_date: Optional[date] = None) -> Optional[float]:
        """
        Convert a price from one currency to another.
        
        Args:
            price: Price to convert
            from_currency: Source currency
            to_currency: Target currency (default: EUR)
            target_date: Specific date for conversion (optional)
            
        Returns:
            Converted price or None if conversion fails
        """
        if price is None:
            return None
        
        rate = self.get_exchange_rate(from_currency, to_currency, target_date)
        if rate is None:
            return None
        
        converted_price = price * rate
        return round(converted_price, 2)
    
    def convert_price_data_batch(self, price_data: List[Dict[str, Any]], from_currency: str) -> List[Dict[str, Any]]:
        """
        Convert all price fields in a list of price data dictionaries to EUR efficiently.
        
        Args:
            price_data: List of dictionaries containing price data
            from_currency: Source currency
            
        Returns:
            List of price data with additional EUR conversion fields
        """
        if from_currency == 'EUR':
            # Already in EUR, add EUR fields with same values
            for data in price_data:
                data.update({
                    'open_eur': data.get('open'),
                    'high_eur': data.get('high'),
                    'low_eur': data.get('low'),
                    'close_eur': data.get('close')
                })
            return price_data
        
        # Get unique dates for batch rate fetching
        unique_dates = list(set(data.get('date') for data in price_data if data.get('date')))
        unique_dates.sort()
        
        if not unique_dates:
            return price_data
        
        # Fetch rates for all unique dates at once
        start_date = datetime.strptime(unique_dates[0], '%Y-%m-%d').date()
        end_date = datetime.strptime(unique_dates[-1], '%Y-%m-%d').date()
        
        rates = self.get_historical_exchange_rates(from_currency, start_date, end_date, 'EUR')
        self.store_exchange_rates(from_currency, 'EUR', rates)
        
        # Convert each price record
        for data in price_data:
            date_str = data.get('date')
            if date_str and date_str in rates:
                rate = rates[date_str]
                data.update({
                    'open_eur': round(data.get('open') * rate, 2) if data.get('open') else None,
                    'high_eur': round(data.get('high') * rate, 2) if data.get('high') else None,
                    'low_eur': round(data.get('low') * rate, 2) if data.get('low') else None,
                    'close_eur': round(data.get('close') * rate, 2) if data.get('close') else None
                })
            else:
                # Fallback to None if rate not available
                data.update({
                    'open_eur': None,
                    'high_eur': None,
                    'low_eur': None,
                    'close_eur': None
                })
        
        return price_data
