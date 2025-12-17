#!/usr/bin/env python3
"""
SQLite to PostgreSQL Sync Script
Syncs data from SQLite database to PostgreSQL for Metabase dashboard
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import sql

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SQLiteToPostgresSync:
    """Sync data from SQLite to PostgreSQL."""
    
    def __init__(self, sqlite_path: str = None, postgres_config: dict = None):
        """
        Initialize sync class.
        
        Args:
            sqlite_path: Path to SQLite database
            postgres_config: PostgreSQL connection config dict
        """
        # Default SQLite path
        if sqlite_path is None:
            # Try analytics/database first, then database/ (root level)
            analytics_path = project_root / "analytics" / "database" / "etf_database.db"
            root_path = project_root / "database" / "etf_database.db"
            if analytics_path.exists():
                sqlite_path = analytics_path
            elif root_path.exists():
                sqlite_path = root_path
            else:
                sqlite_path = analytics_path  # Default to analytics path for error message
        self.sqlite_path = sqlite_path
        
        # Default PostgreSQL config (from environment or defaults)
        if postgres_config is None:
            self.pg_config = {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': os.getenv('POSTGRES_PORT', '5432'),
                'database': os.getenv('POSTGRES_DB', 'stock_market'),
                'user': os.getenv('POSTGRES_USER', 'metabase'),
                'password': os.getenv('POSTGRES_PASSWORD', 'metabase_password')
            }
        else:
            self.pg_config = postgres_config
    
    def connect_sqlite(self):
        """Connect to SQLite database."""
        if not os.path.exists(self.sqlite_path):
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_path}")
        return sqlite3.connect(self.sqlite_path)
    
    def connect_postgres(self):
        """Connect to PostgreSQL database."""
        try:
            conn = psycopg2.connect(**self.pg_config)
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def get_symbol_id_mapping(self, sqlite_conn, pg_conn):
        """Create a mapping from SQLite symbol_id to PostgreSQL symbol_id based on ticker."""
        sqlite_cur = sqlite_conn.cursor()
        pg_cur = pg_conn.cursor()
        
        # Get SQLite symbols with their IDs and tickers
        sqlite_cur.execute("SELECT id, ticker FROM symbols")
        sqlite_symbols = {ticker: sqlite_id for sqlite_id, ticker in sqlite_cur.fetchall()}
        
        # Get PostgreSQL symbols with their IDs and tickers
        pg_cur.execute("SELECT id, ticker FROM symbols")
        pg_symbols = {ticker: pg_id for pg_id, ticker in pg_cur.fetchall()}
        
        # Create mapping: sqlite_id -> pg_id
        mapping = {}
        for ticker, sqlite_id in sqlite_symbols.items():
            if ticker in pg_symbols:
                mapping[sqlite_id] = pg_symbols[ticker]
        
        return mapping
    
    def sync_table(self, table_name: str, sqlite_conn, pg_conn, 
                   columns: list, batch_size: int = 1000, symbol_id_mapping: dict = None):
        """
        Sync a table from SQLite to PostgreSQL.
        
        Args:
            table_name: Name of the table to sync
            columns: List of column names to sync
            sqlite_conn: SQLite connection
            pg_conn: PostgreSQL connection
            batch_size: Number of rows to insert per batch
        """
        logger.info(f"Syncing table: {table_name}")
        
        # Read from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        query = f"SELECT {', '.join(columns)} FROM {table_name}"
        sqlite_cursor.execute(query)
        
        # Get all rows and convert types for PostgreSQL
        raw_rows = sqlite_cursor.fetchall()
        rows = []
        for row in raw_rows:
            converted_row = list(row)
            # Convert boolean fields (SQLite uses 0/1, PostgreSQL needs True/False)
            if 'is_active' in columns:
                is_active_idx = columns.index('is_active')
                converted_row[is_active_idx] = bool(converted_row[is_active_idx])
            
            # Remap symbol_id if needed
            if symbol_id_mapping and 'symbol_id' in columns:
                symbol_id_idx = columns.index('symbol_id')
                sqlite_symbol_id = converted_row[symbol_id_idx]
                if sqlite_symbol_id in symbol_id_mapping:
                    converted_row[symbol_id_idx] = symbol_id_mapping[sqlite_symbol_id]
                else:
                    # Skip rows with unmapped symbol_ids
                    continue
            
            rows.append(tuple(converted_row))
        
        logger.info(f"  Found {len(raw_rows)} rows in SQLite, {len(rows)} rows after mapping")
        
        if len(rows) == 0:
            logger.info(f"  No data to sync for {table_name}")
            return
        
        # Write to PostgreSQL (upsert)
        pg_cursor = pg_conn.cursor()
        
        # Build upsert query
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        # Determine unique constraint based on table
        if table_name == 'symbols':
            conflict_col = 'id'  # Use id for symbols
        elif table_name == 'currency_rates':
            conflict_col = 'id'  # Use id for currency_rates
        elif table_name == 'etf_data':
            conflict_col = '(symbol_id, date)'  # Composite unique key
        elif table_name == 'fifty_two_week_metrics':
            conflict_col = '(symbol_id, calculation_date)'  # Composite unique key
        elif table_name == 'decrease_thresholds':
            conflict_col = '(symbol_id, calculation_date)'  # Composite unique key
        elif 'id' in columns:
            conflict_col = 'id'
        else:
            conflict_col = columns[0]
        
        # Build update clause
        update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id' and col not in conflict_col.replace('(', '').replace(')', '').split(', ')])
        
        upsert_query = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT {conflict_col if '(' in conflict_col else f'({conflict_col})'} DO UPDATE SET
            {update_clause}
        """
        
        # Insert in batches
        total_inserted = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            try:
                # Use individual inserts for better error handling
                for row in batch:
                    try:
                        pg_cursor.execute(upsert_query, row)
                        total_inserted += 1
                    except Exception as e2:
                        logger.debug(f"  Skipping row due to error: {e2}")
                        continue
            except Exception as e:
                logger.error(f"Error inserting batch for {table_name}: {e}")
                # Try individual inserts for this batch
                for row in batch:
                    try:
                        pg_cursor.execute(upsert_query, row)
                        total_inserted += 1
                    except Exception as e2:
                        logger.debug(f"  Skipping row due to error: {e2}")
                        continue
        
        pg_conn.commit()
        logger.info(f"  Synced {total_inserted} rows to PostgreSQL")
    
    def sync_all_tables(self):
        """Sync all main tables from SQLite to PostgreSQL."""
        logger.info("Starting SQLite to PostgreSQL sync...")
        
        sqlite_conn = self.connect_sqlite()
        pg_conn = self.connect_postgres()
        
        try:
            # Define tables and their columns
            # Note: For PostgreSQL, we include 'id' to match SQLite IDs, but use ON CONFLICT
            tables = {
                'symbols': ['id', 'isin', 'ticker', 'name', 'asset_type', 'exchange', 'currency', 'created_at', 'is_active'],
                'currency_rates': ['id', 'from_currency', 'to_currency', 'rate_date', 'exchange_rate', 'created_at'],
                'etf_data': ['id', 'symbol_id', 'date', 'open', 'high', 'low', 'close', 'volume', 
                            'open_eur', 'high_eur', 'low_eur', 'close_eur', 'created_at'],
                'fifty_two_week_metrics': ['id', 'symbol_id', 'calculation_date', 'high_52week', 
                                           'low_52week', 'high_date', 'low_date', 'created_at'],
                'decrease_thresholds': ['id', 'symbol_id', 'calculation_date', 'high_52week_price',
                                       'decrease_5_price', 'decrease_10_price', 'decrease_15_price',
                                       'decrease_20_price', 'decrease_25_price', 'decrease_30_price', 'created_at']
            }
            
            # Get symbol_id mapping (needed for tables with foreign keys to symbols)
            symbol_id_mapping = self.get_symbol_id_mapping(sqlite_conn, pg_conn)
            logger.info(f"Created symbol_id mapping: {len(symbol_id_mapping)} symbols")
            
            # Sync each table
            for table_name, columns in tables.items():
                try:
                    # Pass mapping for tables that reference symbols
                    mapping = symbol_id_mapping if 'symbol_id' in columns else None
                    self.sync_table(table_name, sqlite_conn, pg_conn, columns, symbol_id_mapping=mapping)
                except Exception as e:
                    logger.error(f"Failed to sync {table_name}: {e}")
                    continue
            
            logger.info("✅ SQLite to PostgreSQL sync completed!")
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            raise
        finally:
            sqlite_conn.close()
            pg_conn.close()


def main():
    """Main function."""
    try:
        sync = SQLiteToPostgresSync()
        sync.sync_all_tables()
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

