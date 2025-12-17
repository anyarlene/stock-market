@echo off
REM Quick script to set up Metabase dashboard via API (Windows)

echo 🚀 Setting up Market Insights Dashboard via Metabase API...
echo.

REM Get credentials
set /p METABASE_URL="Metabase URL (default: http://localhost:3000): "
if "%METABASE_URL%"=="" set METABASE_URL=http://localhost:3000

set /p METABASE_USERNAME="Metabase Username: "
set /p METABASE_PASSWORD="Metabase Password: "

REM Run the script
python dashboard\data-export\metabase_api.py --url "%METABASE_URL%" --username "%METABASE_USERNAME%" --password "%METABASE_PASSWORD%"

echo.
echo ✅ Dashboard setup complete!
pause

