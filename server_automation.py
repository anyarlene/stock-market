#!/usr/bin/env python3
"""
Server Automation Script
Runs the market data workflow and commits changes to Git
Designed to run on a server or cloud platform
"""

import subprocess
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Run a shell command and log the result."""
    try:
        logger.info(f"🔄 {description}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {description} completed successfully")
            if result.stdout:
                logger.info(f"Output: {result.stdout.strip()}")
        else:
            logger.error(f"❌ {description} failed")
            logger.error(f"Error: {result.stderr}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"❌ Error in {description}: {e}")
        return False

def main():
    """Main automation function."""
    logger.info("🚀 Starting server automation")
    
    # Step 1: Pull latest changes from Git
    if not run_command("git pull", "Pulling latest changes from Git"):
        return False
    
    # Step 2: Run the market data update
    if not run_command("python analytics/enhanced_workflow.py --step incremental", "Running market data update"):
        return False
    
    # Step 3: Add changes to Git
    if not run_command("git add analytics/database/etf_database.db analytics/logs/", "Adding changes to Git"):
        return False
    
    # Step 4: Commit changes
    commit_message = f"Daily market data update {datetime.now().strftime('%Y-%m-%d')}"
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        logger.info("No changes to commit")
    
    # Step 5: Push changes
    if not run_command("git push", "Pushing changes to remote"):
        return False
    
    logger.info("✅ Server automation completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
