import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import pandas as pd

class DatabaseManager:
    def __init__(self, db_path: str = "data/etf_database.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Create a database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def disconnect(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def initialize_database(self):
        """Create database tables from schema.sql."""
        try:
            with open('analytics/data/schema.sql', 'r') as schema_file:
                schema = schema_file.read()
                self.connect()
                self.conn.executescript(schema)
                self.conn.commit()
        except (sqlite3.Error, IOError) as e:
            print(f"Error initializing database: {e}")
            raise
        finally:
            self.disconnect()

    def insert_etf_data(self, etf_isin: str, data: pd.DataFrame):
        """Insert ETF price data into the database."""
        try:
            self.connect()
            for index, row in data.iterrows():
                self.cursor.execute("""
                    INSERT OR REPLACE INTO etf_data 
                    (etf_isin, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    etf_isin,
                    index.strftime('%Y-%m-%d'),
                    row['Open'],
                    row['High'],
                    row['Low'],
                    row['Close'],
                    row['Volume']
                ))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error inserting ETF data: {e}")
            raise
        finally:
            self.disconnect()

    def update_52week_metrics(self, etf_isin: str, calculation_date: date):
        """Calculate and update 52-week high/low metrics."""
        try:
            self.connect()
            
            # Get 52 weeks of data
            self.cursor.execute("""
                SELECT date, high, low
                FROM etf_data
                WHERE etf_isin = ?
                AND date <= ?
                AND date > date(?, '-52 weeks')
                ORDER BY date DESC
            """, (etf_isin, calculation_date, calculation_date))
            
            data = self.cursor.fetchall()
            if not data:
                return
            
            # Calculate 52-week high and low
            high_52week = max(row[1] for row in data)
            low_52week = min(row[2] for row in data)
            high_date = next(row[0] for row in data if row[1] == high_52week)
            low_date = next(row[0] for row in data if row[2] == low_52week)
            
            # Insert or update metrics
            self.cursor.execute("""
                INSERT OR REPLACE INTO fifty_two_week_metrics
                (etf_isin, calculation_date, high_52week, low_52week, high_date, low_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (etf_isin, calculation_date, high_52week, low_52week, high_date, low_date))
            
            # Calculate and insert decrease thresholds
            decreases = {
                10: high_52week * 0.9,
                15: high_52week * 0.85,
                20: high_52week * 0.8,
                25: high_52week * 0.75,
                30: high_52week * 0.7
            }
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO decrease_thresholds
                (etf_isin, calculation_date, high_52week_price, 
                decrease_10_price, decrease_15_price, decrease_20_price,
                decrease_25_price, decrease_30_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                etf_isin, calculation_date, high_52week,
                decreases[10], decreases[15], decreases[20],
                decreases[25], decreases[30]
            ))
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating 52-week metrics: {e}")
            raise
        finally:
            self.disconnect()

    def get_latest_metrics(self, etf_isin: str) -> Optional[Dict[str, Any]]:
        """Get the latest metrics for an ETF."""
        try:
            self.connect()
            
            self.cursor.execute("""
                SELECT 
                    m.calculation_date,
                    m.high_52week,
                    m.low_52week,
                    d.decrease_10_price,
                    d.decrease_15_price,
                    d.decrease_20_price,
                    d.decrease_25_price,
                    d.decrease_30_price,
                    e.close as current_price
                FROM fifty_two_week_metrics m
                JOIN decrease_thresholds d ON m.etf_isin = d.etf_isin 
                    AND m.calculation_date = d.calculation_date
                JOIN etf_data e ON m.etf_isin = e.etf_isin
                WHERE m.etf_isin = ?
                ORDER BY m.calculation_date DESC, e.date DESC
                LIMIT 1
            """, (etf_isin,))
            
            row = self.cursor.fetchone()
            if not row:
                return None
                
            return {
                'calculation_date': row[0],
                'high_52week': row[1],
                'low_52week': row[2],
                'decrease_10_price': row[3],
                'decrease_15_price': row[4],
                'decrease_20_price': row[5],
                'decrease_25_price': row[6],
                'decrease_30_price': row[7],
                'current_price': row[8]
            }
            
        except sqlite3.Error as e:
            print(f"Error getting latest metrics: {e}")
            raise
        finally:
            self.disconnect()

    def get_price_history(self, etf_isin: str, start_date: Optional[date] = None) -> pd.DataFrame:
        """Get price history for an ETF."""
        try:
            self.connect()
            
            query = """
                SELECT date, open, high, low, close, volume
                FROM etf_data
                WHERE etf_isin = ?
            """
            params = [etf_isin]
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
                
            query += " ORDER BY date"
            
            df = pd.read_sql_query(query, self.conn, params=params, parse_dates=['date'])
            df.set_index('date', inplace=True)
            return df
            
        except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
            print(f"Error getting price history: {e}")
            raise
        finally:
            self.disconnect()