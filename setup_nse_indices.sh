#!/bin/bash
# One-command setup for NSE index classification
# Runs complete pipeline: schema -> scraper -> classifier

set -e  # Exit on error

echo "======================================================================="
echo "NSE INDEX CLASSIFICATION - ONE-COMMAND SETUP"
echo "======================================================================="
echo ""

# Change to project root
cd "$(dirname "$0")"

# Check Python version
echo "🐍 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found!"; exit 1; }

# Check database exists
if [ ! -f "market_data.db" ]; then
    echo "❌ market_data.db not found!"
    echo "   Run upstox_instruments_fetcher_v2.py first"
    exit 1
fi

echo "✅ Database found"
echo ""

# Step 1: Schema migration
echo "======================================================================="
echo "STEP 1: SCHEMA MIGRATION"
echo "======================================================================="
python3 scripts/etl/schema_indices_v1.py
echo ""

# Step 2: NSE index scraper
echo "======================================================================="
echo "STEP 2: NSE INDEX SCRAPER (CSV + HTML)"
echo "======================================================================="
echo "⏱️  This will take 2-3 minutes (rate limited)"
python3 scripts/etl/nse_index_scraper.py
echo ""

# Step 3: Index classifier
echo "======================================================================="
echo "STEP 3: INDEX CLASSIFIER"
echo "======================================================================="
python3 scripts/etl/nse_index_classifier.py
echo ""

# Summary
echo "======================================================================="
echo "✅ NSE INDEX CLASSIFICATION COMPLETE"
echo "======================================================================="
echo ""
echo "Next steps:"
echo "  1. Query classified stocks:"
echo "     SELECT * FROM instruments_tier1 WHERE is_nifty50 = 1;"
echo ""
echo "  2. Filter by sector:"
echo "     SELECT * FROM instruments_tier1 WHERE sector = 'Technology';"
echo ""
echo "  3. Schedule monthly auto-refresh:"
echo "     python3 -c \"from scripts.data_sync_manager import DataSyncManager; mgr = DataSyncManager(); mgr.schedule_nse_indices_sync(); mgr.run_scheduler()\""
echo ""
echo "  4. Or use orchestrator directly:"
echo "     python3 scripts/etl/nse_index_orchestrator.py"
echo ""
echo "======================================================================="
