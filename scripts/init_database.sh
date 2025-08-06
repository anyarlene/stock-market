#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p data

# Initialize the database using Python
python - << EOF
from analytics.database.db_manager import DatabaseManager

def init_db():
    print("Initializing database...")
    db = DatabaseManager()
    db.initialize_database()
    
    # Add initial symbols
    symbols = [
        {
            'isin': 'IE00BFMXXD54',
            'ticker': 'VUAA.L',
            'name': 'Vanguard S&P 500 UCITS ETF',
            'asset_type': 'ETF',
            'exchange': 'LSE',
            'currency': 'USD'
        },
        {
            'isin': 'IE00B53SZB19',
            'ticker': 'VUKE.L',
            'name': 'Vanguard FTSE 100 UCITS ETF',
            'asset_type': 'ETF',
            'exchange': 'LSE',
            'currency': 'GBP'
        }
    ]
    
    for symbol in symbols:
        print(f"Adding symbol: {symbol['name']}")
        db.add_symbol(**symbol)
    
    print("Database initialization completed!")

if __name__ == "__main__":
    init_db()
EOF