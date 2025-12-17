#!/usr/bin/env python3
"""
Initialize PostgreSQL Database
Creates schema and views for Metabase dashboard
"""

import os
import sys
import logging
from pathlib import Path
import psycopg2
from psycopg2 import sql

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_postgres_database(postgres_config: dict = None):
    """
    Initialize PostgreSQL database with schema and views.
    
    Args:
        postgres_config: PostgreSQL connection config dict
    """
    if postgres_config is None:
        pg_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'stock_market'),
            'user': os.getenv('POSTGRES_USER', 'metabase'),
            'password': os.getenv('POSTGRES_PASSWORD', 'metabase_password')
        }
    else:
        pg_config = postgres_config
    
    try:
        # Connect to PostgreSQL
        logger.info("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**pg_config)
        cursor = conn.cursor()
        
        # Read and execute schema SQL
        schema_path = Path(__file__).parent / "postgresql_schema.sql"
        if schema_path.exists():
            logger.info("Creating database schema...")
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            cursor.execute(schema_sql)
            conn.commit()
            logger.info("✅ Database schema created")
        else:
            logger.warning(f"Schema file not found: {schema_path}")
        
        # Read and execute views SQL
        views_path = Path(__file__).parent / "dashboard_views.sql"
        if views_path.exists():
            logger.info("Creating database views...")
            with open(views_path, 'r') as f:
                views_sql = f.read()
            cursor.execute(views_sql)
            conn.commit()
            logger.info("✅ Database views created")
        else:
            logger.warning(f"Views file not found: {views_path}")
        
        cursor.close()
        conn.close()
        
        logger.info("✅ PostgreSQL database initialized successfully!")
        
    except psycopg2.Error as e:
        logger.error(f"Error initializing PostgreSQL database: {e}")
        raise


def main():
    """Main function."""
    try:
        init_postgres_database()
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

