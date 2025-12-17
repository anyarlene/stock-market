#!/bin/bash
# Quick script to set up Metabase dashboard via API

echo "🚀 Setting up Market Insights Dashboard via Metabase API..."
echo ""

# Get credentials
read -p "Metabase URL (default: http://localhost:3000): " METABASE_URL
METABASE_URL=${METABASE_URL:-http://localhost:3000}

read -p "Metabase Username: " METABASE_USERNAME
read -s -p "Metabase Password: " METABASE_PASSWORD
echo ""

# Run the script
python dashboard/data-export/metabase_api.py \
    --url "$METABASE_URL" \
    --username "$METABASE_USERNAME" \
    --password "$METABASE_PASSWORD"

echo ""
echo "✅ Dashboard setup complete!"

