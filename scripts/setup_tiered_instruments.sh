#!/bin/bash
# Quick Setup Script - Tiered Instruments System V2
# Run this to set up the new tiered instruments architecture

set -e  # Exit on error

echo "======================================================================"
echo "TIERED INSTRUMENTS SYSTEM - SETUP SCRIPT"
echo "======================================================================"
echo ""

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Navigate to project root
cd "$(dirname "$0")"

echo ""
echo "Step 1/4: Creating tiered database schema..."
echo "----------------------------------------------------------------------"
python3 scripts/schema_migration_v3.py

echo ""
echo "Step 2/4: Fetching instruments from Upstox CDN (JSON format)..."
echo "----------------------------------------------------------------------"
echo "   This will download ~200K instruments and filter into tiers"
echo "   Expected time: 30-60 seconds"
echo ""
python3 scripts/etl/upstox_instruments_fetcher_v2.py

echo ""
echo "Step 3/4: Running index labeling & enrichment..."
echo "----------------------------------------------------------------------"
echo "   - Marking F&O availability"
echo "   - Labeling NIFTY50 stocks"
echo "   - Adding sector/industry data (sample)"
echo ""
python3 scripts/etl/index_labeling_utility.py

echo ""
echo "Step 4/4: Verifying installation..."
echo "----------------------------------------------------------------------"
python3 -c "
import sqlite3
conn = sqlite3.connect('market_data.db')
cur = conn.cursor()

tables = ['instruments_tier1', 'instruments_sme', 'instruments_derivatives', 'instruments_indices_etfs']
print('\n📊 Database Status:')
print('-' * 60)
for table in tables:
    cur.execute(f'SELECT COUNT(*) FROM {table}')
    count = cur.fetchone()[0]
    print(f'{table:35} | {count:,} rows')

print('-' * 60)

# F&O stats
cur.execute('SELECT COUNT(*) FROM instruments_tier1 WHERE has_fno = 1')
fno_count = cur.fetchone()[0]
print(f'Tier1 stocks with F&O:                | {fno_count:,}')

# NIFTY50 stats
cur.execute('SELECT COUNT(*) FROM instruments_tier1 WHERE is_nifty50 = 1')
nifty50_count = cur.fetchone()[0]
print(f'NIFTY 50 stocks marked:               | {nifty50_count:,}')

print('-' * 60)
print('✅ Setup complete!')
conn.close()
"

echo ""
echo "======================================================================"
echo "✅ TIERED INSTRUMENTS SYSTEM READY!"
echo "======================================================================"
echo ""
echo "📚 What was created:"
echo "   • instruments_tier1       - Liquid equity (NSE EQ + BSE A/B/XT)"
echo "   • instruments_sme         - SME stocks with risk flags"
echo "   • instruments_derivatives - F&O contracts with auto-expiry"
echo "   • instruments_indices_etfs- Market indices & ETFs"
echo ""
echo "🔄 Automated sync:"
echo "   • Scheduled: Daily at 6:30 AM IST"
echo "   • Format: JSON (CSV deprecated)"
echo "   • Source: Upstox CDN (complete.json.gz)"
echo ""
echo "🎯 Next steps:"
echo "   1. Configure DataSyncManager for automation:"
echo "      python3 -c \"from scripts.data_sync_manager import DataSyncManager; mgr = DataSyncManager(); mgr.schedule_instruments_sync(); mgr.run_scheduler()\""
echo ""
echo "   2. Query instruments in your code:"
echo "      SELECT * FROM instruments_tier1 WHERE has_fno = 1 AND is_nifty50 = 1"
echo ""
echo "   3. Update sector/industry data:"
echo "      • Implement NSE scraper for full sector mapping"
echo "      • Load NIFTY100/200/500 constituents"
echo ""
echo "   4. Build frontend filters:"
echo "      • Sector dropdown"
echo "      • Index membership filter (NIFTY50/100/200)"
echo "      • F&O availability toggle"
echo ""
echo "📖 Configuration: config/trading.yaml (instruments section)"
echo "======================================================================"
