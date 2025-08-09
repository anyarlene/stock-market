"""Database manager for ETF analytics."""

import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import pandas as pd
import os
import time
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "analytics/database/etf_database.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
    def connect(self):
        """Create a database connection."""
        try:
            if self.conn is None:
                self.conn = sqlite3.connect(self.db_path)
                self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def disconnect(self):
        """Close the database connection."""
        try:
            if self.conn:
                self.conn.close()
        finally:
            self.conn = None
            self.cursor = None

    def initialize_database(self):
        """Create database tables from schema.sql."""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r') as schema_file:
                schema = schema_file.read()
                self.connect()
                self.conn.executescript(schema)
                self.conn.commit()
                print(f"Database initialized at: {os.path.abspath(self.db_path)}")
        except (sqlite3.Error, IOError) as e:
            print(f"Error initializing database: {e}")
            raise
        finally:
            self.disconnect()

    def get_market_data_range(self, symbol_id: int, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get market data for a symbol within a date range."""
        try:
            self.connect()
            self.cursor.execute("""
                SELECT date, open, high, low, close, volume
                FROM etf_data
                WHERE symbol_id = ?
                AND date BETWEEN ? AND ?
                ORDER BY date
            """, (symbol_id, start_date, end_date))
            
            columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting market data: {e}")
            raise
        finally:
            self.disconnect()

    def get_active_symbols(self) -> List[Dict[str, Any]]:
        """Get all active symbols from the database."""
        try:
            self.connect()
            self.cursor.execute("""
                SELECT id, isin, ticker, name, asset_type, exchange, currency
                FROM symbols
                WHERE is_active = 1
                ORDER BY name
            """)
            
            columns = ['id', 'isin', 'ticker', 'name', 'asset_type', 'exchange', 'currency']
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Error getting active symbols: {e}")
            raise
        finally:
            self.disconnect()

    def get_symbol_by_isin(self, isin: str) -> Optional[Dict[str, Any]]:
        """Get symbol information by ISIN."""
        try:
            self.connect()
            self.cursor.execute("""
                SELECT id, isin, ticker, name, asset_type, exchange, currency, is_active
                FROM symbols
                WHERE isin = ?
            """, (isin,))
            
            row = self.cursor.fetchone()
            if not row:
                return None
                
            return {
                'id': row[0],
                'isin': row[1],
                'ticker': row[2],
                'name': row[3],
                'asset_type': row[4],
                'exchange': row[5],
                'currency': row[6],
                'is_active': row[7]
            }
            
        except sqlite3.Error as e:
            print(f"Error getting symbol by ISIN: {e}")
            raise
        finally:
            self.disconnect()

    def add_symbol(self, isin: str, ticker: str, name: str, 
                  asset_type: str, exchange: str, currency: str) -> int:
        """Add a new symbol to the database."""
        try:
            self.connect()
            self.cursor.execute("""
                INSERT INTO symbols (isin, ticker, name, asset_type, exchange, currency)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (isin, ticker, name, asset_type, exchange, currency))
            
            symbol_id = self.cursor.lastrowid
            self.conn.commit()
            return symbol_id
            
        except sqlite3.Error as e:
            print(f"Error adding symbol: {e}")
            raise
        finally:
            self.disconnect()

    def clear_symbols(self):
        """Clear all symbols from the database."""
        try:
            self.connect()
            self.cursor.execute("DELETE FROM symbols")
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error clearing symbols: {e}")
            raise
        finally:
            self.disconnect()

    def insert_market_data(self, symbol_id: int, data: pd.DataFrame, currency: str = None):
        """
        Insert market data into the database with EUR conversion.
        
        Args:
            symbol_id: Symbol ID
            data: DataFrame with OHLCV data
            currency: Currency of the data (USD, GBP, EUR)
        """
        try:
            from analytics.utils.currency_converter import CurrencyConverter
            
            converter = CurrencyConverter()
            self.connect()
            
            # Convert DataFrame to list of dictionaries for batch processing
            price_data_list = []
            for index, row in data.iterrows():
                price_record = {
                    'date': index.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                }
                price_data_list.append(price_record)
            
            # Batch convert to EUR if needed
            if currency and currency != 'EUR':
                logger.info(f"Converting {len(price_data_list)} price records from {currency} to EUR")
                price_data_list = converter.convert_price_data_batch(price_data_list, currency)
            
            # Insert all records
            for price_data in price_data_list:
                self.cursor.execute("""
                    INSERT OR REPLACE INTO etf_data 
                    (symbol_id, date, open, high, low, close, volume, open_eur, high_eur, low_eur, close_eur)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol_id,
                    price_data['date'],
                    price_data['open'],
                    price_data['high'],
                    price_data['low'],
                    price_data['close'],
                    price_data['volume'],
                    price_data.get('open_eur'),
                    price_data.get('high_eur'),
                    price_data.get('low_eur'),
                    price_data.get('close_eur')
                ))
            
            self.conn.commit()
            logger.info(f"Successfully inserted {len(price_data_list)} records for symbol {symbol_id}")
            
        except sqlite3.Error as e:
            print(f"Error inserting market data: {e}")
            raise
        finally:
            self.disconnect()

    def store_52week_metrics(self, symbol_id: int, calculation_date: date,
                           high_52week: float, low_52week: float,
                           high_date: date, low_date: date):
        """Store 52-week metrics and calculate decrease thresholds."""
        try:
            self.connect()
            
            # Store metrics
            self.cursor.execute("""
                INSERT OR REPLACE INTO fifty_two_week_metrics
                (symbol_id, calculation_date, high_52week, low_52week, high_date, low_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (symbol_id, calculation_date, high_52week, low_52week, high_date, low_date))
            
            # Calculate decrease thresholds
            decreases = {
                10: high_52week * 0.9,
                15: high_52week * 0.85,
                20: high_52week * 0.8,
                25: high_52week * 0.75,
                30: high_52week * 0.7
            }
            
            # Store thresholds
            self.cursor.execute("""
                INSERT OR REPLACE INTO decrease_thresholds
                (symbol_id, calculation_date, high_52week_price, 
                decrease_10_price, decrease_15_price, decrease_20_price,
                decrease_25_price, decrease_30_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol_id, calculation_date, high_52week,
                decreases[10], decreases[15], decreases[20],
                decreases[25], decreases[30]
            ))
            
            self.conn.commit()
            logger.info(f"Stored metrics and thresholds for symbol {symbol_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Error storing metrics: {e}")
            raise
        finally:
            self.disconnect()