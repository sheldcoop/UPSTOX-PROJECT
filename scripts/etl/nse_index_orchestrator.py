#!/usr/bin/env python3
"""
NSE Index Orchestrator
Coordinates the complete NSE index classification pipeline:
1. Schema migration (if needed)
2. Scrape all 18 NSE indices (CSV + HTML)
3. Classify and map to instruments_tier1
4. Validation and reporting
"""

import sqlite3
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "market_data.db"
SCHEMA_SCRIPT = PROJECT_ROOT / "scripts" / "schema_indices_v1.py"
SCRAPER_SCRIPT = PROJECT_ROOT / "scripts" / "etl" / "nse_index_scraper.py"
CLASSIFIER_SCRIPT = PROJECT_ROOT / "scripts" / "etl" / "nse_index_classifier.py"


class NSEIndexOrchestrator:
    """
    Orchestrates complete NSE index classification workflow
    - Validates prerequisites
    - Runs schema migration
    - Executes scraper
    - Runs classifier
    - Validates results
    - Logs to database
    """
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        self.execution_log = {
            'start_time': datetime.now(),
            'end_time': None,
            'status': 'RUNNING',
            'schema_migration': None,
            'scraper': None,
            'classifier': None,
            'validation': None,
            'errors': []
        }
        
        # Expected index counts (for validation)
        self.expected_counts = {
            'NIFTY50': 50,
            'NIFTYNEXT50': 50,
            'NIFTY100': 100,
            'NIFTY200': 200,
            'NIFTY500': 500,
            'NIFTYMIDCAP150': 150,
            'NIFTYMIDCAP100': 100,
            'NIFTYMIDCAP50': 50,
            'NIFTYSMALLCAP500': 500,
            'NIFTYSMALLCAP250': 250,
            'NIFTYSMALLCAP100': 100,
            'NIFTYTOTALMARKET': 750,
        }
    
    def check_prerequisites(self) -> bool:
        """Validate all required files and dependencies"""
        logger.info("=" * 70)
        logger.info("PREREQUISITE CHECKS")
        logger.info("=" * 70)
        
        checks_passed = True
        
        # Check database exists
        if not self.db_path.exists():
            logger.error(f"❌ Database not found: {self.db_path}")
            checks_passed = False
        else:
            logger.info(f"✅ Database found: {self.db_path}")
        
        # Check instruments_tier1 has data
        self.cursor.execute("SELECT COUNT(*) FROM instruments_tier1")
        tier1_count = self.cursor.fetchone()[0]
        
        if tier1_count == 0:
            logger.error("❌ instruments_tier1 is empty!")
            logger.info("   Run upstox_instruments_fetcher_v2.py first")
            checks_passed = False
        else:
            logger.info(f"✅ instruments_tier1: {tier1_count:,} stocks")
        
        # Check script files exist
        scripts = [
            ('Schema Migration', SCHEMA_SCRIPT),
            ('NSE Scraper', SCRAPER_SCRIPT),
            ('Index Classifier', CLASSIFIER_SCRIPT)
        ]
        
        for name, path in scripts:
            if not path.exists():
                logger.error(f"❌ {name} not found: {path}")
                checks_passed = False
            else:
                logger.info(f"✅ {name}: {path.name}")
        
        # Check Python packages
        try:
            import requests
            import pandas
            import bs4
            logger.info("✅ Required packages: requests, pandas, beautifulsoup4")
        except ImportError as e:
            logger.error(f"❌ Missing package: {e}")
            checks_passed = False
        
        logger.info("")
        return checks_passed
    
    def run_schema_migration(self) -> bool:
        """Execute schema migration script"""
        logger.info("=" * 70)
        logger.info("STEP 1: SCHEMA MIGRATION")
        logger.info("=" * 70)
        
        try:
            # Check if migration already done
            self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='nse_index_metadata'
            """)
            
            if self.cursor.fetchone():
                logger.info("✅ Schema already migrated (nse_index_metadata exists)")
                self.execution_log['schema_migration'] = 'SKIPPED'
                return True
            
            # Run migration
            logger.info(f"🔧 Running: {SCHEMA_SCRIPT.name}")
            result = subprocess.run(
                [sys.executable, str(SCHEMA_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("✅ Schema migration completed")
                logger.info(result.stdout)
                self.execution_log['schema_migration'] = 'SUCCESS'
                return True
            else:
                logger.error(f"❌ Schema migration failed (exit code {result.returncode})")
                logger.error(result.stderr)
                self.execution_log['schema_migration'] = 'FAILED'
                self.execution_log['errors'].append(f"Schema: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Schema migration timed out")
            self.execution_log['schema_migration'] = 'TIMEOUT'
            return False
        except Exception as e:
            logger.error(f"❌ Schema migration error: {e}")
            self.execution_log['schema_migration'] = 'ERROR'
            self.execution_log['errors'].append(f"Schema: {str(e)}")
            return False
    
    def run_scraper(self) -> bool:
        """Execute NSE index scraper"""
        logger.info("\n" + "=" * 70)
        logger.info("STEP 2: NSE INDEX SCRAPER")
        logger.info("=" * 70)
        
        try:
            logger.info(f"🕷️  Running: {SCRAPER_SCRIPT.name}")
            logger.info("   This will download CSVs and scrape HTML for all 18 indices")
            logger.info("   Estimated time: 2-3 minutes (rate limited)")
            
            result = subprocess.run(
                [sys.executable, str(SCRAPER_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            if result.returncode == 0:
                logger.info("✅ Scraper completed")
                logger.info(result.stdout)
                self.execution_log['scraper'] = 'SUCCESS'
                return True
            else:
                logger.error(f"❌ Scraper failed (exit code {result.returncode})")
                logger.error(result.stderr)
                self.execution_log['scraper'] = 'FAILED'
                self.execution_log['errors'].append(f"Scraper: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Scraper timed out (>5 minutes)")
            self.execution_log['scraper'] = 'TIMEOUT'
            return False
        except Exception as e:
            logger.error(f"❌ Scraper error: {e}")
            self.execution_log['scraper'] = 'ERROR'
            self.execution_log['errors'].append(f"Scraper: {str(e)}")
            return False
    
    def run_classifier(self) -> bool:
        """Execute index classifier"""
        logger.info("\n" + "=" * 70)
        logger.info("STEP 3: INDEX CLASSIFIER")
        logger.info("=" * 70)
        
        try:
            logger.info(f"🏷️  Running: {CLASSIFIER_SCRIPT.name}")
            logger.info("   This will map constituents to instruments_tier1")
            
            result = subprocess.run(
                [sys.executable, str(CLASSIFIER_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes max
            )
            
            if result.returncode == 0:
                logger.info("✅ Classifier completed")
                logger.info(result.stdout)
                self.execution_log['classifier'] = 'SUCCESS'
                return True
            else:
                logger.error(f"❌ Classifier failed (exit code {result.returncode})")
                logger.error(result.stderr)
                self.execution_log['classifier'] = 'FAILED'
                self.execution_log['errors'].append(f"Classifier: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Classifier timed out (>2 minutes)")
            self.execution_log['classifier'] = 'TIMEOUT'
            return False
        except Exception as e:
            logger.error(f"❌ Classifier error: {e}")
            self.execution_log['classifier'] = 'ERROR'
            self.execution_log['errors'].append(f"Classifier: {str(e)}")
            return False
    
    def validate_results(self) -> bool:
        """Validate classification results"""
        logger.info("\n" + "=" * 70)
        logger.info("STEP 4: VALIDATION")
        logger.info("=" * 70)
        
        try:
            validation_passed = True
            
            # Check index_constituents_v2 has data
            self.cursor.execute("""
            SELECT COUNT(DISTINCT index_code), COUNT(*), COUNT(DISTINCT instrument_key)
            FROM index_constituents_v2
            WHERE is_active = 1
            """)
            
            indices_count, total_mappings, unique_instruments = self.cursor.fetchone()
            
            logger.info(f"📊 Database status:")
            logger.info(f"  Indices classified:      {indices_count}")
            logger.info(f"  Total mappings:          {total_mappings:,}")
            logger.info(f"  Unique instruments:      {unique_instruments:,}")
            
            if indices_count == 0:
                logger.error("❌ No indices classified!")
                validation_passed = False
            
            # Validate key indices have expected counts
            logger.info(f"\n🔍 Validating constituent counts:")
            
            for index_code, expected in self.expected_counts.items():
                self.cursor.execute("""
                SELECT COUNT(*) 
                FROM index_constituents_v2
                WHERE index_code = ? AND is_active = 1
                """, (index_code,))
                
                actual = self.cursor.fetchone()[0]
                tolerance = 0.1  # Allow 10% variance
                
                if actual == 0:
                    logger.warning(f"  ⚠️  {index_code:20} | Expected: {expected:3}, Got: {actual:3} (MISSING)")
                elif abs(actual - expected) / expected > tolerance:
                    logger.warning(f"  ⚠️  {index_code:20} | Expected: {expected:3}, Got: {actual:3} (VARIANCE)")
                else:
                    logger.info(f"  ✅ {index_code:20} | Expected: {expected:3}, Got: {actual:3}")
            
            # Check tier1 flags
            self.cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_nifty50 = 1 THEN 1 ELSE 0 END) as nifty50,
                SUM(CASE WHEN is_nifty100 = 1 THEN 1 ELSE 0 END) as nifty100,
                SUM(CASE WHEN is_nifty500 = 1 THEN 1 ELSE 0 END) as nifty500,
                SUM(CASE WHEN is_midcap = 1 THEN 1 ELSE 0 END) as midcap,
                SUM(CASE WHEN is_smallcap = 1 THEN 1 ELSE 0 END) as smallcap,
                SUM(CASE WHEN sector IS NOT NULL THEN 1 ELSE 0 END) as with_sector
            FROM instruments_tier1
            WHERE is_active = 1
            """)
            
            flags = self.cursor.fetchone()
            
            logger.info(f"\n🚩 Tier1 flags updated:")
            logger.info(f"  is_nifty50:      {flags[0]:4}")
            logger.info(f"  is_nifty100:     {flags[1]:4}")
            logger.info(f"  is_nifty500:     {flags[2]:4}")
            logger.info(f"  is_midcap:       {flags[3]:4}")
            logger.info(f"  is_smallcap:     {flags[4]:4}")
            logger.info(f"  with_sector:     {flags[5]:4}")
            
            # Sample classified stocks
            logger.info(f"\n📋 Sample NIFTY 50 stocks:")
            self.cursor.execute("""
            SELECT symbol, sector, industry, index_memberships
            FROM instruments_tier1
            WHERE is_nifty50 = 1 AND is_active = 1
            ORDER BY symbol
            LIMIT 5
            """)
            
            for symbol, sector, industry, memberships in self.cursor.fetchall():
                logger.info(f"  {symbol:15} | {sector or '-':20} | {memberships or '-'}")
            
            self.execution_log['validation'] = 'SUCCESS' if validation_passed else 'WARNINGS'
            return validation_passed
            
        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            self.execution_log['validation'] = 'ERROR'
            self.execution_log['errors'].append(f"Validation: {str(e)}")
            return False
    
    def log_execution(self):
        """Log execution to nse_index_scrape_log table"""
        try:
            self.cursor.execute("""
            INSERT INTO nse_index_scrape_log 
            (index_code, scrape_timestamp, status, constituents_count, csv_success, html_success, error_message)
            VALUES (?, datetime('now'), ?, ?, ?, ?, ?)
            """, (
                'ORCHESTRATOR',
                self.execution_log['status'],
                0,
                1 if self.execution_log['schema_migration'] == 'SUCCESS' else 0,
                1 if self.execution_log['classifier'] == 'SUCCESS' else 0,
                ', '.join(self.execution_log['errors']) if self.execution_log['errors'] else None
            ))
            self.conn.commit()
        except Exception as e:
            logger.warning(f"⚠️  Could not log execution: {e}")
    
    def run_pipeline(self):
        """Execute complete classification pipeline"""
        logger.info("\n" + "=" * 70)
        logger.info("NSE INDEX ORCHESTRATOR - COMPLETE PIPELINE")
        logger.info("=" * 70)
        logger.info(f"Start time: {self.execution_log['start_time']}")
        logger.info("")
        
        # Step 0: Prerequisites
        if not self.check_prerequisites():
            logger.error("\n❌ Prerequisites check failed")
            logger.info("   Fix errors above and try again")
            self.execution_log['status'] = 'FAILED'
            return False
        
        # Step 1: Schema migration
        if not self.run_schema_migration():
            logger.error("\n❌ Pipeline stopped at schema migration")
            self.execution_log['status'] = 'FAILED'
            self.log_execution()
            return False
        
        # Step 2: Scraper
        if not self.run_scraper():
            logger.error("\n❌ Pipeline stopped at scraper")
            self.execution_log['status'] = 'FAILED'
            self.log_execution()
            return False
        
        # Step 3: Classifier
        if not self.run_classifier():
            logger.error("\n❌ Pipeline stopped at classifier")
            self.execution_log['status'] = 'FAILED'
            self.log_execution()
            return False
        
        # Step 4: Validation
        validation_ok = self.validate_results()
        
        # Final summary
        self.execution_log['end_time'] = datetime.now()
        duration = (self.execution_log['end_time'] - self.execution_log['start_time']).total_seconds()
        
        logger.info("\n" + "=" * 70)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Start time:         {self.execution_log['start_time']}")
        logger.info(f"End time:           {self.execution_log['end_time']}")
        logger.info(f"Duration:           {duration:.1f} seconds ({duration/60:.1f} minutes)")
        logger.info(f"Schema migration:   {self.execution_log['schema_migration']}")
        logger.info(f"Scraper:            {self.execution_log['scraper']}")
        logger.info(f"Classifier:         {self.execution_log['classifier']}")
        logger.info(f"Validation:         {self.execution_log['validation']}")
        
        if self.execution_log['errors']:
            logger.info(f"\n⚠️  Errors encountered:")
            for error in self.execution_log['errors']:
                logger.info(f"  - {error}")
        
        if validation_ok:
            self.execution_log['status'] = 'SUCCESS'
            logger.info("\n✅ PIPELINE COMPLETED SUCCESSFULLY!")
            logger.info("\nNext steps:")
            logger.info("  1. Query classified stocks: SELECT * FROM instruments_tier1 WHERE is_nifty50 = 1")
            logger.info("  2. Filter by sector: SELECT * FROM instruments_tier1 WHERE sector = 'Technology'")
            logger.info("  3. Schedule monthly refresh in DataSyncManager")
        else:
            self.execution_log['status'] = 'SUCCESS_WITH_WARNINGS'
            logger.info("\n⚠️  Pipeline completed with warnings")
            logger.info("   Review validation output above")
        
        logger.info("=" * 70)
        
        self.log_execution()
        return True
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """CLI entry point"""
    orchestrator = NSEIndexOrchestrator()
    
    try:
        success = orchestrator.run_pipeline()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Pipeline interrupted by user")
        orchestrator.execution_log['status'] = 'INTERRUPTED'
        orchestrator.log_execution()
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        orchestrator.execution_log['status'] = 'ERROR'
        orchestrator.execution_log['errors'].append(str(e))
        orchestrator.log_execution()
        sys.exit(1)
    finally:
        orchestrator.close()


if __name__ == "__main__":
    main()
