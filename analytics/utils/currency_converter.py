#!/usr/bin/env python3
"""
Currency Converter Utility

This module handles currency conversions for ETF data, specifically converting
USD and GBP prices to EUR for European market analysis.
"""

import yfinance as yf
from datetime import datetime, date
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CurrencyConverter:
    """Handles currency conversions for ETF data."""
    
    def __init__(self):
        self.exchange_rates = {}
        self.last_update = None
    
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
        
        # For now, use current rates (we can enhance with historical rates later)
        try:
            # Use yfinance for exchange rates
            if from_currency == 'USD' and to_currency == 'EUR':
                symbol = 'USDEUR=X'
            elif from_currency == 'GBP' and to_currency == 'EUR':
                symbol = 'GBPEUR=X'
            else:
                logger.warning(f"Unsupported currency pair: {from_currency}/{to_currency}")
                return None
            
            ticker = yf.Ticker(symbol)
            
            # Get current rate (for historical data, we'd need to fetch historical rates)
            if target_date:
                # For historical rates, we'd need to implement historical rate fetching
                # For now, use current rate as approximation
                logger.info(f"Using current rate for historical date {target_date} (approximation)")
            
            # Get the most recent rate
            hist = ticker.history(period='1d')
            if hist.empty:
                logger.error(f"Could not fetch exchange rate for {symbol}")
                return None
            
            rate = float(hist['Close'].iloc[-1])
            logger.debug(f"Exchange rate {from_currency}/{to_currency}: {rate}")
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching exchange rate for {from_currency}/{to_currency}: {e}")
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
    
    def convert_price_data(self, price_data: Dict[str, Any], from_currency: str) -> Dict[str, Any]:
        """
        Convert all price fields in a price data dictionary to EUR.
        
        Args:
            price_data: Dictionary containing price data
            from_currency: Source currency
            
        Returns:
            Price data with additional EUR conversion fields
        """
        if from_currency == 'EUR':
            # Already in EUR, add EUR fields with same values
            price_data.update({
                'open_eur': price_data.get('open'),
                'high_eur': price_data.get('high'),
                'low_eur': price_data.get('low'),
                'close_eur': price_data.get('close')
            })
            return price_data
        
        # Convert to EUR
        converted_data = price_data.copy()
        converted_data.update({
            'open_eur': self.convert_price(price_data.get('open'), from_currency),
            'high_eur': self.convert_price(price_data.get('high'), from_currency),
            'low_eur': self.convert_price(price_data.get('low'), from_currency),
            'close_eur': self.convert_price(price_data.get('close'), from_currency)
        })
        
        return converted_data
