#!/usr/bin/env python3
"""
One-Click Market Database Setup
Sets up complete market data database with NSE indices
"""

import sqlite3
import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "market_data.db"
SCHEMA_FILE = PROJECT_ROOT / "scripts" / "database" / "schema.sql"
NSE_FETCHER = PROJECT_ROOT / "scripts" / "etl" / "nse_indices_fetcher.py"


def print_header():
    """Print setup header"""
    print("\n" + "=" * 70)
    print("🚀 UPSTOX TRADING PLATFORM - MARKET DATABASE SETUP")
    print("=" * 70)
    print()


def check_prerequisites():
    """Check if all required files exist"""
    logger.info("Checking prerequisites...")
    
    if not SCHEMA_FILE.exists():
        logger.error(f"❌ Schema file not found: {SCHEMA_FILE}")
        return False
    
    if not NSE_FETCHER.exists():
        logger.error(f"❌ NSE fetcher not found: {NSE_FETCHER}")
        return False
    
    logger.info("✅ All prerequisites met")
    return True


def create_schema():
    """Create database schema"""
    logger.info("Creating database schema...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Read and execute schema
        with open(SCHEMA_FILE, 'r') as f:
            schema_sql = f.read()
        
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        logger.info("✅ Database schema created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating schema: {e}")
        return False


def fetch_nse_data():
    """Run NSE indices fetcher"""
    logger.info("Fetching NSE indices data...")
    logger.info("This may take 2-3 minutes...\n")
    
    try:
        result = subprocess.run(
            [sys.executable, str(NSE_FETCHER)],
            cwd=PROJECT_ROOT,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("\n✅ NSE data fetched successfully")
            return True
        else:
            logger.error(f"\n❌ NSE fetcher failed with code {result.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running NSE fetcher: {e}")
        return False


def verify_setup():
    """Verify database setup"""
    logger.info("\nVerifying database setup...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = [
            'instruments', 'index_master', 'index_constituents',
            'sectors', 'stock_sectors', 'derivatives_metadata'
        ]
        
        missing = [t for t in required_tables if t not in tables]
        if missing:
            logger.error(f"❌ Missing tables: {', '.join(missing)}")
            return False
        
        logger.info("✅ All required tables present")
        
        # Check data
        cursor.execute("SELECT COUNT(*) FROM index_master")
        index_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM index_constituents WHERE is_active = 1")
        constituent_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sectors")
        sector_count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"✅ Indices: {index_count}")
        logger.info(f"✅ Constituents: {constituent_count}")
        logger.info(f"✅ Sectors: {sector_count}")
        
        if constituent_count == 0:
            logger.warning("⚠️  No constituents found - NSE fetch may have failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def print_next_steps():
    """Print next steps"""
    print("\n" + "=" * 70)
    print("✅ DATABASE SETUP COMPLETE!")
    print("=" * 70)
    print("\nNext Steps:")
    print("  1. Test movers service:")
    print("     python scripts/utilities/test_movers_service.py")
    print()
    print("  2. Start the platform:")
    print("     python run_platform.py")
    print()
    print("  3. Open dashboard:")
    print("     http://localhost:5001")
    print()
    print("  4. Check Market Movers on home page")
    print("=" * 70)
    print()


def main():
    """Main setup flow"""
    print_header()
    
    # Step 1: Check prerequisites
    if not check_prerequisites():
        logger.error("Setup failed - missing prerequisites")
        sys.exit(1)
    
    # Step 2: Create schema
    if not create_schema():
        logger.error("Setup failed - schema creation error")
        sys.exit(1)
    
    # Step 3: Fetch NSE data
    if not fetch_nse_data():
        logger.error("Setup failed - NSE data fetch error")
        sys.exit(1)
    
    # Step 4: Verify
    if not verify_setup():
        logger.error("Setup failed - verification error")
        sys.exit(1)
    
    # Success!
    print_next_steps()


if __name__ == "__main__":
    main()
