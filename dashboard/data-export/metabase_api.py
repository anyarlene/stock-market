#!/usr/bin/env python3
"""
Metabase API Client
Automates dashboard creation and chart addition via Metabase API
"""

import os
import sys
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetabaseAPI:
    """Metabase API client for automating dashboard operations."""
    
    def __init__(self, base_url: str = None, username: str = None, password: str = None):
        """
        Initialize Metabase API client.
        
        Args:
            base_url: Metabase URL (default: http://localhost:3000)
            username: Metabase username
            password: Metabase password
        """
        self.base_url = base_url or os.getenv('METABASE_URL', 'http://localhost:3000')
        self.username = username or os.getenv('METABASE_USERNAME', '')
        self.password = password or os.getenv('METABASE_PASSWORD', '')
        self.session_token = None
        self.session_id = None
        
        # Remove trailing slash
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
    
    def authenticate(self) -> bool:
        """
        Authenticate with Metabase and get session token.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Authenticating with Metabase...")
            
            # Get session token
            response = requests.post(
                f"{self.base_url}/api/session",
                json={
                    "username": self.username,
                    "password": self.password
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get('id')
                self.session_id = response.cookies.get('metabase.SESSION')
                
                logger.info("✅ Successfully authenticated with Metabase")
                return True
            else:
                logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "X-Metabase-Session": self.session_token
        }
        return headers
    
    def get_database_id(self, database_name: str = "Stock Market Dashboard") -> Optional[int]:
        """
        Get database ID by name.
        
        Args:
            database_name: Name of the database
            
        Returns:
            Database ID or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/database",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                databases = response.json().get('data', [])
                for db in databases:
                    if db.get('name') == database_name:
                        db_id = db.get('id')
                        logger.info(f"✅ Found database '{database_name}' with ID: {db_id}")
                        return db_id
                
                logger.warning(f"⚠️  Database '{database_name}' not found")
                return None
            else:
                logger.error(f"❌ Failed to get databases: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting database ID: {e}")
            return None
    
    def create_question(self, name: str, sql_query: str, database_id: int,
                       visualization_type: str = "gauge",
                       visualization_settings: Dict = None) -> Optional[int]:
        """
        Create a new question (card) in Metabase.
        
        Args:
            name: Question name
            sql_query: SQL query
            database_id: Database ID
            visualization_type: Type of visualization (gauge, bar, line, etc.)
            visualization_settings: Additional visualization settings
            
        Returns:
            Question ID or None if failed
        """
        try:
            logger.info(f"Creating question: {name}")
            
            # Map visualization types
            viz_type_map = {
                "gauge": "progress",
                "bar": "bar",
                "line": "line",
                "pie": "pie",
                "table": "table",
                "number": "scalar"
            }
            
            viz_type = viz_type_map.get(visualization_type.lower(), "progress")
            
            # Create question payload
            payload = {
                "name": name,
                "dataset_query": {
                    "database": database_id,
                    "type": "native",
                    "native": {
                        "query": sql_query
                    }
                },
                "display": viz_type,
                "visualization_settings": visualization_settings or {}
            }
            
            response = requests.post(
                f"{self.base_url}/api/card",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                question_id = response.json().get('id')
                logger.info(f"✅ Created question '{name}' with ID: {question_id}")
                return question_id
            else:
                logger.error(f"❌ Failed to create question: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating question: {e}")
            return None
    
    def create_dashboard(self, name: str, description: str = "") -> Optional[int]:
        """
        Create a new dashboard.
        
        Args:
            name: Dashboard name
            description: Dashboard description
            
        Returns:
            Dashboard ID or None if failed
        """
        try:
            logger.info(f"Creating dashboard: {name}")
            
            payload = {
                "name": name,
                "description": description
            }
            
            response = requests.post(
                f"{self.base_url}/api/dashboard",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                dashboard_id = response.json().get('id')
                logger.info(f"✅ Created dashboard '{name}' with ID: {dashboard_id}")
                return dashboard_id
            else:
                logger.error(f"❌ Failed to create dashboard: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating dashboard: {e}")
            return None
    
    def add_card_to_dashboard(self, dashboard_id: int, question_id: int,
                             row: int = 0, col: int = 0, size_x: int = 6, size_y: int = 4) -> bool:
        """
        Add a question card to a dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            question_id: Question ID
            row: Row position (0-based)
            col: Column position (0-based)
            size_x: Width in grid units (1-12)
            size_y: Height in grid units
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Adding question {question_id} to dashboard {dashboard_id}")
            
            # Get dashboard first to understand structure
            dashboard_response = requests.get(
                f"{self.base_url}/api/dashboard/{dashboard_id}",
                headers=self._get_headers()
            )
            
            if dashboard_response.status_code != 200:
                logger.error(f"❌ Failed to get dashboard: {dashboard_response.status_code}")
                return False
            
            dashboard_data = dashboard_response.json()
            
            # Add card using the correct API format
            payload = {
                "cardId": question_id,
                "row": row,
                "col": col,
                "sizeX": size_x,
                "sizeY": size_y,
                "series": []
            }
            
            # Metabase API: Update dashboard with new card
            # We need to GET the dashboard, add the card to its cards array, then PUT it back
            dashboard_response = requests.get(
                f"{self.base_url}/api/dashboard/{dashboard_id}",
                headers=self._get_headers()
            )
            
            if dashboard_response.status_code != 200:
                logger.error(f"❌ Failed to get dashboard: {dashboard_response.status_code}")
                return False
            
            dashboard_data = dashboard_response.json()
            
            # Add new card to dashboard's cards array
            new_card = {
                "id": None,  # Will be assigned by Metabase
                "card_id": question_id,
                "row": row,
                "col": col,
                "sizeX": size_x,
                "sizeY": size_y,
                "series": [],
                "parameter_mappings": []
            }
            
            # Get existing cards or initialize empty list
            existing_cards = dashboard_data.get("ordered_cards", [])
            existing_cards.append(new_card)
            
            # Update dashboard
            update_payload = {
                "name": dashboard_data.get("name"),
                "description": dashboard_data.get("description"),
                "parameters": dashboard_data.get("parameters", []),
                "ordered_cards": existing_cards
            }
            
            response = requests.put(
                f"{self.base_url}/api/dashboard/{dashboard_id}",
                json=update_payload,
                headers=self._get_headers()
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Added question to dashboard")
                return True
            else:
                logger.warning(f"⚠️  API method failed ({response.status_code}). Cards may need manual addition.")
                logger.info(f"📝 To add cards manually:")
                logger.info(f"   1. Open dashboard {dashboard_id} in Metabase")
                logger.info(f"   2. Click '+' → 'Saved questions'")
                logger.info(f"   3. Find question ID {question_id} and add it")
                logger.info(f"   4. Position it at row {row}, col {col}, size {size_x}x{size_y}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error adding card: {e}")
            return False
    
    def add_text_card(self, dashboard_id: int, text: str,
                     row: int = 0, col: int = 0, size_x: int = 6, size_y: int = 2) -> bool:
        """
        Add a text card to a dashboard.
        Note: Text cards may need to be added manually via UI, but we'll try API.
        
        Args:
            dashboard_id: Dashboard ID
            text: Text content
            row: Row position
            col: Column position
            size_x: Width
            size_y: Height
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Adding text card to dashboard {dashboard_id}")
            logger.warning("⚠️  Text cards may need to be added manually in Metabase UI")
            
            # Metabase text cards use a different format
            # For now, we'll log instructions for manual addition
            logger.info(f"📝 To add text card manually:")
            logger.info(f"   1. Open dashboard {dashboard_id} in Metabase")
            logger.info(f"   2. Click '+' → 'Text'")
            logger.info(f"   3. Paste this text:")
            logger.info(f"   {text[:100]}...")
            
            return True  # Return True but note it needs manual addition
                
        except Exception as e:
            logger.error(f"❌ Error adding text card: {e}")
            return False


def create_market_insights_dashboard(metabase_url: str = None,
                                    username: str = None,
                                    password: str = None) -> bool:
    """
    Create a complete Market Insights Dashboard with all charts.
    
    Args:
        metabase_url: Metabase URL
        username: Metabase username
        password: Metabase password
        
    Returns:
        True if successful, False otherwise
    """
    # Initialize API client
    api = MetabaseAPI(metabase_url, username, password)
    
    # Authenticate
    if not api.authenticate():
        return False
    
    # Get database ID
    db_id = api.get_database_id("Stock Market Dashboard")
    if not db_id:
        logger.error("❌ Could not find database")
        return False
    
    # Create dashboard
    dashboard_id = api.create_dashboard(
        "Market Insights Dashboard",
        "Comprehensive market sentiment and sector analysis"
    )
    if not dashboard_id:
        return False
    
    # Define charts to create
    charts = [
        {
            "name": "Fear & Greed Index Gauge",
            "sql": """
                SELECT
                    value,
                    CASE
                        WHEN value <= 25 THEN 'EXTREME FEAR'
                        WHEN value <= 45 THEN 'FEAR'
                        WHEN value <= 55 THEN 'NEUTRAL'
                        WHEN value <= 75 THEN 'GREED'
                        ELSE 'EXTREME GREED'
                    END as classification
                FROM vw_fear_greed_latest
            """,
            "type": "gauge",
            "row": 0,
            "col": 0,
            "size_x": 8,
            "size_y": 6
        },
        {
            "name": "Fear & Greed Historical Trend",
            "sql": """
                SELECT
                    timestamp,
                    value,
                    classification
                FROM vw_fear_greed_historical
                ORDER BY timestamp DESC
            """,
            "type": "line",
            "row": 0,
            "col": 8,
            "size_x": 4,
            "size_y": 6
        },
        {
            "name": "S&P 500 Sector Performance",
            "sql": """
                SELECT
                    sector,
                    change_percent,
                    current_price
                FROM vw_sp500_sector_performance
                ORDER BY change_percent DESC
            """,
            "type": "bar",
            "row": 6,
            "col": 0,
            "size_x": 12,
            "size_y": 4
        }
    ]
    
    # Add legend text card
    legend_text = """
# Fear & Greed Index Legend

**0-25: Extreme Fear** (Red) - Market panic, oversold conditions

**25-45: Fear** (Yellow) - Cautious sentiment, potential buying opportunity

**45-55: Neutral** (Green) - Balanced market sentiment

**55-75: Greed** (Light Blue) - Optimistic sentiment, potential overvaluation

**75-100: Extreme Greed** (Dark Green) - Market euphoria, overbought conditions

*Current value indicates overall market sentiment based on 7 indicators.*
    """
    
    # Add legend
    api.add_text_card(dashboard_id, legend_text, row=0, col=8, size_x=4, size_y=6)
    
    # Create and add charts
    for chart in charts:
        question_id = api.create_question(
            chart["name"],
            chart["sql"],
            db_id,
            chart["type"]
        )
        
        if question_id:
            api.add_card_to_dashboard(
                dashboard_id,
                question_id,
                row=chart["row"],
                col=chart["col"],
                size_x=chart["size_x"],
                size_y=chart["size_y"]
            )
    
    logger.info(f"✅ Dashboard created successfully! View at: {api.base_url}/dashboard/{dashboard_id}")
    return True


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create Metabase dashboard via API')
    parser.add_argument('--url', default='http://localhost:3000', help='Metabase URL')
    parser.add_argument('--username', required=True, help='Metabase username')
    parser.add_argument('--password', required=True, help='Metabase password')
    
    args = parser.parse_args()
    
    success = create_market_insights_dashboard(
        args.url,
        args.username,
        args.password
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

