"""Database manager for ETF analytics."""

import os
import psycopg2
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def _build_database_url() -> str:
    """Build the PostgreSQL connection URL from environment variables."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    user = os.environ.get("DB_USER", "etf_user")
    password = os.environ.get("DB_PASSWORD", "etf_pass")
    dbname = os.environ.get("DB_NAME", "etf_db")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


class DatabaseManager:
    def __init__(self, database_url: str = None):
        """Initialize with a PostgreSQL connection URL."""
        self.database_url = database_url or _build_database_url()
        self.conn = None
        self.cursor = None

    def connect(self):
        """Open a database connection."""
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(self.database_url)
                self.cursor = self.conn.cursor()
        except psycopg2.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def disconnect(self):
        """Close the database connection."""
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
        finally:
            self.conn = None
            self.cursor = None

    def initialize_database(self):
        """Create database tables from schema.sql."""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            with open(schema_path, "r") as f:
                schema = f.read()
            self.connect()
            # psycopg2 does not support executescript; run each statement separately
            statements = [s.strip() for s in schema.split(";") if s.strip()]
            for stmt in statements:
                self.cursor.execute(stmt)
            self.conn.commit()
            logger.info("Database initialized successfully")
            print("Database initialized successfully")
        except (psycopg2.Error, IOError) as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            self.disconnect()

    def get_market_data_range(
        self, symbol_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Get market data for a symbol within a date range."""
        try:
            self.connect()
            self.cursor.execute(
                """
                SELECT date, open, high, low, close, volume
                FROM etf_data
                WHERE symbol_id = %s AND date BETWEEN %s AND %s
                ORDER BY date
            """,
                (symbol_id, start_date, end_date),
            )
            columns = ["date", "open", "high", "low", "close", "volume"]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except psycopg2.Error as e:
            logger.error(f"Error getting market data: {e}")
            raise
        finally:
            self.disconnect()

    def get_active_symbols(self) -> List[Dict[str, Any]]:
        """Get all active symbols from the database."""
        try:
            self.connect()
            self.cursor.execute(
                """
                SELECT id, isin, ticker, name, asset_type, exchange, currency
                FROM symbols
                WHERE is_active = TRUE
                ORDER BY name
            """
            )
            columns = ["id", "isin", "ticker", "name", "asset_type", "exchange", "currency"]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except psycopg2.Error as e:
            logger.error(f"Error getting active symbols: {e}")
            raise
        finally:
            self.disconnect()

    def get_symbol_by_isin(self, isin: str) -> Optional[Dict[str, Any]]:
        """Get symbol information by ISIN."""
        try:
            self.connect()
            self.cursor.execute(
                """
                SELECT id, isin, ticker, name, asset_type, exchange, currency, is_active
                FROM symbols
                WHERE isin = %s
            """,
                (isin,),
            )
            row = self.cursor.fetchone()
            if not row:
                return None
            return dict(
                zip(
                    ["id", "isin", "ticker", "name", "asset_type", "exchange", "currency", "is_active"],
                    row,
                )
            )
        except psycopg2.Error as e:
            logger.error(f"Error getting symbol by ISIN: {e}")
            raise
        finally:
            self.disconnect()

    def add_symbol(
        self,
        isin: str,
        ticker: str,
        name: str,
        asset_type: str,
        exchange: str,
        currency: str,
    ) -> int:
        """Add a new symbol to the database and return its ID."""
        try:
            self.connect()
            self.cursor.execute(
                """
                INSERT INTO symbols (isin, ticker, name, asset_type, exchange, currency)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
                (isin, ticker, name, asset_type, exchange, currency),
            )
            symbol_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return symbol_id
        except psycopg2.Error as e:
            logger.error(f"Error adding symbol: {e}")
            raise
        finally:
            self.disconnect()

    def clear_symbols(self):
        """Clear all symbols from the database."""
        try:
            self.connect()
            self.cursor.execute("DELETE FROM symbols")
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Error clearing symbols: {e}")
            raise
        finally:
            self.disconnect()

    def insert_market_data(self, symbol_id: int, data: pd.DataFrame, currency: str = None):
        """Insert market data with optional EUR conversion."""
        try:
            from analytics.utils.currency_converter import CurrencyConverter

            converter = CurrencyConverter()
            self.connect()

            price_data_list = []
            for index, row in data.iterrows():
                price_data_list.append(
                    {
                        "date": index.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    }
                )

            if currency and currency != "EUR":
                logger.info(f"Converting {len(price_data_list)} records from {currency} to EUR")
                price_data_list = converter.convert_price_data_batch(price_data_list, currency)

            for price_data in price_data_list:
                self.cursor.execute(
                    """
                    INSERT INTO etf_data
                        (symbol_id, date, open, high, low, close, volume,
                         open_eur, high_eur, low_eur, close_eur)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol_id, date) DO UPDATE SET
                        open        = EXCLUDED.open,
                        high        = EXCLUDED.high,
                        low         = EXCLUDED.low,
                        close       = EXCLUDED.close,
                        volume      = EXCLUDED.volume,
                        open_eur    = EXCLUDED.open_eur,
                        high_eur    = EXCLUDED.high_eur,
                        low_eur     = EXCLUDED.low_eur,
                        close_eur   = EXCLUDED.close_eur
                """,
                    (
                        symbol_id,
                        price_data["date"],
                        price_data["open"],
                        price_data["high"],
                        price_data["low"],
                        price_data["close"],
                        price_data["volume"],
                        price_data.get("open_eur"),
                        price_data.get("high_eur"),
                        price_data.get("low_eur"),
                        price_data.get("close_eur"),
                    ),
                )

            self.conn.commit()
            logger.info(f"Inserted {len(price_data_list)} records for symbol {symbol_id}")

        except psycopg2.Error as e:
            logger.error(f"Error inserting market data: {e}")
            raise
        finally:
            self.disconnect()

    def store_52week_metrics(
        self,
        symbol_id: int,
        calculation_date: date,
        high_52week: float,
        low_52week: float,
        high_date: date,
        low_date: date,
    ):
        """Store 52-week metrics and calculate decrease thresholds."""
        try:
            self.connect()

            self.cursor.execute(
                """
                INSERT INTO fifty_two_week_metrics
                    (symbol_id, calculation_date, high_52week, low_52week, high_date, low_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol_id, calculation_date) DO UPDATE SET
                    high_52week = EXCLUDED.high_52week,
                    low_52week  = EXCLUDED.low_52week,
                    high_date   = EXCLUDED.high_date,
                    low_date    = EXCLUDED.low_date
            """,
                (symbol_id, calculation_date, high_52week, low_52week, high_date, low_date),
            )

            decreases = {
                5: high_52week * 0.95,
                10: high_52week * 0.90,
                15: high_52week * 0.85,
                20: high_52week * 0.80,
                25: high_52week * 0.75,
                30: high_52week * 0.70,
            }

            self.cursor.execute(
                """
                INSERT INTO decrease_thresholds
                    (symbol_id, calculation_date, high_52week_price,
                     decrease_5_price, decrease_10_price, decrease_15_price,
                     decrease_20_price, decrease_25_price, decrease_30_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol_id, calculation_date) DO UPDATE SET
                    high_52week_price  = EXCLUDED.high_52week_price,
                    decrease_5_price   = EXCLUDED.decrease_5_price,
                    decrease_10_price  = EXCLUDED.decrease_10_price,
                    decrease_15_price  = EXCLUDED.decrease_15_price,
                    decrease_20_price  = EXCLUDED.decrease_20_price,
                    decrease_25_price  = EXCLUDED.decrease_25_price,
                    decrease_30_price  = EXCLUDED.decrease_30_price
            """,
                (
                    symbol_id,
                    calculation_date,
                    high_52week,
                    decreases[5],
                    decreases[10],
                    decreases[15],
                    decreases[20],
                    decreases[25],
                    decreases[30],
                ),
            )

            self.conn.commit()
            logger.info(f"Stored metrics and thresholds for symbol {symbol_id}")

        except psycopg2.Error as e:
            logger.error(f"Error storing metrics: {e}")
            raise
        finally:
            self.disconnect()
