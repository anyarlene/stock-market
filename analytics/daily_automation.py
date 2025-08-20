#!/usr/bin/env python3
"""
Simple Daily Automation Script
Runs the market data workflow daily at 10 PM Berlin time
"""

import schedule
import time
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analytics/logs/automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def run_daily_update():
    """Run the daily market data update."""
    try:
        logger.info("🚀 Starting daily market data update")
        
        # Import and run the workflow
        from analytics.enhanced_workflow import EnhancedWorkflowOrchestrator
        
        orchestrator = EnhancedWorkflowOrchestrator()
        success = orchestrator.run_incremental_update()
        
        if success:
            logger.info("✅ Daily update completed successfully")
        else:
            logger.error("❌ Daily update failed")
            
    except Exception as e:
        logger.error(f"❌ Error in daily update: {e}")

def main():
    """Main function to run the scheduler."""
    logger.info("🕐 Starting daily automation scheduler")
    logger.info("📅 Scheduled to run daily at 22:00 (10 PM Berlin time)")
    
    # Schedule the job to run daily at 10 PM Berlin time
    schedule.every().day.at("22:00").do(run_daily_update)
    
    # Run once immediately for testing
    logger.info("🧪 Running initial test...")
    run_daily_update()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
