@echo off
REM Quick setup and test script for Metabase dashboard (Windows)

echo 🚀 Starting Metabase Dashboard Setup...
echo.

REM Step 1: Start Docker services
echo 📦 Starting Docker services...
cd dashboard
docker-compose up -d

REM Wait for services to start
echo ⏳ Waiting for services to initialize (30 seconds)...
timeout /t 30 /nobreak >nul

REM Check if services are running
echo.
echo 🔍 Checking service status...
docker-compose ps

REM Step 2: Initialize database
echo.
echo 🗄️  Initializing PostgreSQL database...
cd ..
python dashboard\data-export\init_postgres_db.py

REM Step 3: Sync data
echo.
echo 🔄 Syncing data from SQLite to PostgreSQL...
python dashboard\data-export\sqlite_to_postgres.py

REM Step 4: Export market insights
echo.
echo 📊 Exporting market insights...
python dashboard\data-export\market_insights_to_db.py

echo.
echo ✅ Setup complete!
echo.
echo 🌐 Access Metabase at: http://localhost:3000
echo.
echo 📝 Next steps:
echo    1. Open http://localhost:3000 in your browser
echo    2. Complete Metabase initial setup
echo    3. Connect to PostgreSQL database:
echo       - Host: postgres (or localhost)
echo       - Port: 5432
echo       - Database: stock_market
echo       - Username: metabase
echo       - Password: metabase_password
echo    4. Sync database schema in Metabase
echo    5. Start building dashboards!

pause

