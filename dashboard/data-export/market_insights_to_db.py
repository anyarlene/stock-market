#!/usr/bin/env python3
"""
Market Insights to PostgreSQL Export
Exports Fear & Greed Index, S&P 500 data, and ETF holdings to PostgreSQL
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import execute_values

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import market insights fetcher
from analytics.etl.market_insights_fetcher import (
    fetch_fear_greed_index,
    fetch_sp500_sector_data,
    fetch_etf_holdings
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketInsightsToDB:
    """Export market insights data to PostgreSQL."""
    
    def __init__(self, postgres_config: dict = None):
        """
        Initialize exporter.
        
        Args:
            postgres_config: PostgreSQL connection config dict
        """
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
    
    def connect_postgres(self):
        """Connect to PostgreSQL database."""
        try:
            conn = psycopg2.connect(**self.pg_config)
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def export_fear_greed_index(self, conn):
        """Export Fear & Greed Index data to PostgreSQL."""
        logger.info("Exporting Fear & Greed Index...")
        
        data = fetch_fear_greed_index()
        if not data:
            logger.warning("No Fear & Greed Index data to export")
            return
        
        cursor = conn.cursor()
        
        try:
            # Export current reading
            current = data.get('current', {})
            if current:
                cursor.execute("""
                    INSERT INTO fear_greed_index (value, classification, timestamp)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (timestamp) DO UPDATE SET
                        value = EXCLUDED.value,
                        classification = EXCLUDED.classification
                """, (
                    current.get('value'),
                    current.get('classification'),
                    datetime.fromisoformat(current.get('timestamp', datetime.now().isoformat()).replace('Z', '+00:00'))
                ))
            
            # Export historical data (last 30 days)
            historical = data.get('historical', [])
            if historical:
                historical_rows = []
                for item in historical:
                    try:
                        timestamp = datetime.fromisoformat(
                            item.get('timestamp', datetime.now().isoformat()).replace('Z', '+00:00')
                        )
                        historical_rows.append((
                            item.get('value'),
                            item.get('classification'),
                            timestamp
                        ))
                    except Exception as e:
                        logger.debug(f"Skipping historical item: {e}")
                        continue
                
                if historical_rows:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO fear_greed_index (value, classification, timestamp)
                        VALUES %s
                        ON CONFLICT (timestamp) DO UPDATE SET
                            value = EXCLUDED.value,
                            classification = EXCLUDED.classification
                        """,
                        historical_rows
                    )
            
            conn.commit()
            logger.info("✅ Fear & Greed Index exported successfully")
            
        except Exception as e:
            logger.error(f"Error exporting Fear & Greed Index: {e}")
            conn.rollback()
            raise
    
    def export_sp500_data(self, conn):
        """Export S&P 500 sector and company data to PostgreSQL."""
        logger.info("Exporting S&P 500 data...")
        
        data = fetch_sp500_sector_data()
        if not data:
            logger.warning("No S&P 500 data to export")
            return
        
        cursor = conn.cursor()
        
        try:
            # Export sectors
            sectors = data.get('sectors', [])
            if sectors:
                sector_rows = []
                for sector in sectors:
                    sector_rows.append((
                        sector.get('sector'),
                        sector.get('ticker'),
                        sector.get('currentPrice'),
                        sector.get('changePercent'),
                        sector.get('marketCap')
                    ))
                
                if sector_rows:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO sp500_sectors (sector, ticker, current_price, change_percent, market_cap, last_updated)
                        VALUES %s
                        ON CONFLICT (sector, last_updated) DO UPDATE SET
                            ticker = EXCLUDED.ticker,
                            current_price = EXCLUDED.current_price,
                            change_percent = EXCLUDED.change_percent,
                            market_cap = EXCLUDED.market_cap
                        """,
                        [(row[0], row[1], row[2], row[3], row[4], datetime.now()) for row in sector_rows]
                    )
            
            # Export companies
            companies = data.get('companies', [])
            if companies:
                # Clear old data first (optional - you might want to keep history)
                cursor.execute("DELETE FROM sp500_companies WHERE last_updated < CURRENT_DATE")
                
                company_rows = []
                for company in companies:
                    company_rows.append((
                        company.get('symbol'),
                        company.get('name'),
                        company.get('sector'),
                        company.get('currentPrice'),
                        company.get('changePercent'),
                        company.get('marketCap'),
                        company.get('weight')
                    ))
                
                if company_rows:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO sp500_companies (symbol, name, sector, current_price, change_percent, market_cap, weight, last_updated)
                        VALUES %s
                        """,
                        [(row[0], row[1], row[2], row[3], row[4], row[5], row[6], datetime.now()) for row in company_rows]
                    )
            
            conn.commit()
            logger.info("✅ S&P 500 data exported successfully")
            
        except Exception as e:
            logger.error(f"Error exporting S&P 500 data: {e}")
            conn.rollback()
            raise
    
    def export_etf_holdings(self, conn):
        """Export ETF holdings data to PostgreSQL."""
        logger.info("Exporting ETF holdings...")
        
        etf_tickers = ["VOO", "QQQ", "VTI", "VUAA.L", "CNDX.L"]
        cursor = conn.cursor()
        
        try:
            # Clear old holdings data
            cursor.execute("DELETE FROM etf_holdings WHERE last_updated < CURRENT_DATE")
            
            total_holdings = 0
            
            for ticker in etf_tickers:
                holdings_data = fetch_etf_holdings(ticker)
                if not holdings_data or not holdings_data.get('holdings'):
                    logger.debug(f"No holdings data for {ticker}")
                    continue
                
                etf_name = holdings_data.get('name', ticker)
                holdings = holdings_data.get('holdings', [])
                
                holding_rows = []
                for holding in holdings:
                    holding_rows.append((
                        ticker,
                        etf_name,
                        holding.get('name'),
                        holding.get('percentage')
                    ))
                
                if holding_rows:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO etf_holdings (etf_ticker, etf_name, holding_name, percentage, last_updated)
                        VALUES %s
                        """,
                        [(row[0], row[1], row[2], row[3], datetime.now()) for row in holding_rows]
                    )
                    total_holdings += len(holding_rows)
                    logger.info(f"  Exported {len(holding_rows)} holdings for {ticker}")
            
            conn.commit()
            logger.info(f"✅ ETF holdings exported successfully ({total_holdings} total holdings)")
            
        except Exception as e:
            logger.error(f"Error exporting ETF holdings: {e}")
            conn.rollback()
            raise
    
    def export_all(self):
        """Export all market insights data to PostgreSQL."""
        logger.info("Starting market insights export to PostgreSQL...")
        
        conn = self.connect_postgres()
        
        try:
            self.export_fear_greed_index(conn)
            self.export_sp500_data(conn)
            self.export_etf_holdings(conn)
            
            logger.info("✅ All market insights data exported successfully!")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise
        finally:
            conn.close()


def main():
    """Main function."""
    try:
        exporter = MarketInsightsToDB()
        exporter.export_all()
    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

