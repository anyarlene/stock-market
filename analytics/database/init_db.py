"""Database initialization script."""

from analytics.database.db_manager import DatabaseManager

def main():
    """Initialize the database with tables."""
    print("Initializing database...")
    db = DatabaseManager()
    db.initialize_database()
    print("Database initialized successfully!")

if __name__ == "__main__":
    main()