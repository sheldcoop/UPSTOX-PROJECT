#!/usr/bin/env python3
"""
Index Labeling & Enrichment Utility
Marks tier1 instruments with index membership (NIFTY50, NIFTY100, etc.)
and populates sector/industry data
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Set

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "market_data.db"


class IndexLabelingUtility:
    """
    Utility to enrich tier1 instruments with:
    1. Index membership (NIFTY50, NIFTY100, NIFTY200, NIFTY500)
    2. F&O availability (cross-reference with derivatives)
    3. Sector/Industry classification (manual or from external sources)
    """
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        self.stats = {
            'nifty50_marked': 0,
            'nifty100_marked': 0,
            'nifty200_marked': 0,
            'nifty500_marked': 0,
            'fno_marked': 0,
            'sector_updated': 0
        }
    
    def mark_fno_availability(self):
        """
        Mark tier1 instruments that have F&O contracts
        Cross-references instruments_derivatives table
        """
        logger.info("🔗 Marking F&O availability in tier1...")
        
        # Update has_fno flag for stocks with derivatives
        self.cursor.execute("""
        UPDATE instruments_tier1
        SET has_fno = 1,
            fno_segment = (
                SELECT DISTINCT segment 
                FROM instruments_derivatives 
                WHERE underlying_key = instruments_tier1.instrument_key
                LIMIT 1
            )
        WHERE instrument_key IN (
            SELECT DISTINCT underlying_key 
            FROM instruments_derivatives
            WHERE underlying_type = 'EQUITY' AND is_active = 1
        )
        """)
        
        self.stats['fno_marked'] = self.cursor.rowcount
        self.conn.commit()
        
        logger.info(f"✅ Marked {self.stats['fno_marked']} stocks with F&O availability")
        
        # Show sample
        self.cursor.execute("""
        SELECT symbol, trading_symbol, fno_segment
        FROM instruments_tier1
        WHERE has_fno = 1
        LIMIT 10
        """)
        
        logger.info("\nSample F&O stocks:")
        for row in self.cursor.fetchall():
            logger.info(f"  {row[0]:15} | {row[1]:20} | {row[2]}")
    
    def mark_index_membership_from_constituents(self):
        """
        Mark index membership using existing index_constituents table
        If you have NSE index constituents loaded
        """
        logger.info("🏷️  Marking index membership from constituents...")
        
        # Check if index_constituents table exists
        self.cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('index_constituents', 'index_constituents_v2')
        """)
        
        if not self.cursor.fetchone():
            logger.warning("⚠️  No index_constituents table found")
            logger.info("   To enable index labeling:")
            logger.info("   1. Load NSE index constituents from NSE website")
            logger.info("   2. Run index scraper scripts")
            logger.info("   3. Populate index_constituents_v2 table")
            return
        
        # NIFTY 50
        self.cursor.execute("""
        UPDATE instruments_tier1
        SET is_nifty50 = 1,
            index_memberships = COALESCE(index_memberships || ',', '') || 'NIFTY50'
        WHERE symbol IN (
            SELECT DISTINCT symbol 
            FROM index_constituents 
            WHERE index_code = 'NIFTY50' AND is_active = 1
        )
        """)
        self.stats['nifty50_marked'] = self.cursor.rowcount
        
        # NIFTY 100
        self.cursor.execute("""
        UPDATE instruments_tier1
        SET is_nifty100 = 1,
            index_memberships = COALESCE(index_memberships || ',', '') || 'NIFTY100'
        WHERE symbol IN (
            SELECT DISTINCT symbol 
            FROM index_constituents 
            WHERE index_code = 'NIFTY100' AND is_active = 1
        )
        """)
        self.stats['nifty100_marked'] = self.cursor.rowcount
        
        # NIFTY 200
        self.cursor.execute("""
        UPDATE instruments_tier1
        SET is_nifty200 = 1,
            index_memberships = COALESCE(index_memberships || ',', '') || 'NIFTY200'
        WHERE symbol IN (
            SELECT DISTINCT symbol 
            FROM index_constituents 
            WHERE index_code = 'NIFTY200' AND is_active = 1
        )
        """)
        self.stats['nifty200_marked'] = self.cursor.rowcount
        
        # NIFTY 500
        self.cursor.execute("""
        UPDATE instruments_tier1
        SET is_nifty500 = 1,
            index_memberships = COALESCE(index_memberships || ',', '') || 'NIFTY500'
        WHERE symbol IN (
            SELECT DISTINCT symbol 
            FROM index_constituents 
            WHERE index_code = 'NIFTY500' AND is_active = 1
        )
        """)
        self.stats['nifty500_marked'] = self.cursor.rowcount
        
        self.conn.commit()
        
        logger.info(f"✅ NIFTY50:  {self.stats['nifty50_marked']} stocks marked")
        logger.info(f"✅ NIFTY100: {self.stats['nifty100_marked']} stocks marked")
        logger.info(f"✅ NIFTY200: {self.stats['nifty200_marked']} stocks marked")
        logger.info(f"✅ NIFTY500: {self.stats['nifty500_marked']} stocks marked")
    
    def manual_mark_nifty50(self):
        """
        Manually mark NIFTY 50 stocks (fallback if no constituents table)
        TODO: Update this list periodically from NSE website
        """
        logger.info("📝 Manually marking NIFTY 50 stocks...")
        logger.warning("⚠️  Using hardcoded NIFTY 50 list - may be outdated!")
        logger.info("   For production: Load from NSE API or website scraper")
        
        # NIFTY 50 constituents (as of Feb 2026 - UPDATE REGULARLY!)
        nifty50_symbols = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
            'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK',
            'LT', 'BAJFINANCE', 'ASIANPAINT', 'MARUTI', 'HCLTECH',
            'AXISBANK', 'TITAN', 'SUNPHARMA', 'ULTRACEMCO', 'NESTLEIND',
            'WIPRO', 'TATAMOTORS', 'ONGC', 'NTPC', 'POWERGRID',
            'JSWSTEEL', 'M&M', 'BAJAJFINSV', 'TECHM', 'INDUSINDBK',
            'ADANIENT', 'ADANIPORTS', 'TATASTEEL', 'HINDALCO', 'COALINDIA',
            'DIVISLAB', 'SBILIFE', 'DRREDDY', 'BRITANNIA', 'APOLLOHOSP',
            'CIPLA', 'EICHERMOT', 'GRASIM', 'HEROMOTOCO', 'SHREECEM',
            'TATACONSUM', 'BAJAJ-AUTO', 'ADANIGREEN', 'SIEMENS', 'PIDILITIND'
        ]
        
        # Mark in database
        placeholders = ','.join(['?' for _ in nifty50_symbols])
        self.cursor.execute(f"""
        UPDATE instruments_tier1
        SET is_nifty50 = 1,
            index_memberships = 'NIFTY50'
        WHERE symbol IN ({placeholders})
        """, nifty50_symbols)
        
        self.stats['nifty50_marked'] = self.cursor.rowcount
        self.conn.commit()
        
        logger.info(f"✅ Manually marked {self.stats['nifty50_marked']}/50 NIFTY 50 stocks")
        
        if self.stats['nifty50_marked'] < 50:
            logger.warning(f"⚠️  Only {self.stats['nifty50_marked']}/50 found - check symbol mappings")
    
    def update_sector_industry_manual(self):
        """
        Manually update sector/industry for key stocks
        TODO: Replace with automated scraper from NSE/BSE
        """
        logger.info("🏭 Updating sector/industry (manual mapping)...")
        logger.warning("⚠️  Using sample sector mapping - implement full NSE scraper for production")
        
        # Sample sector/industry mappings
        sector_mappings = [
            # Banking
            ('HDFCBANK', 'Financial Services', 'Private Banks'),
            ('ICICIBANK', 'Financial Services', 'Private Banks'),
            ('SBIN', 'Financial Services', 'Public Banks'),
            ('KOTAKBANK', 'Financial Services', 'Private Banks'),
            ('AXISBANK', 'Financial Services', 'Private Banks'),
            
            # IT
            ('TCS', 'Technology', 'IT Services'),
            ('INFY', 'Technology', 'IT Services'),
            ('WIPRO', 'Technology', 'IT Services'),
            ('HCLTECH', 'Technology', 'IT Services'),
            ('TECHM', 'Technology', 'IT Services'),
            
            # Energy
            ('RELIANCE', 'Energy', 'Oil & Gas Refining'),
            ('ONGC', 'Energy', 'Oil & Gas Exploration'),
            ('NTPC', 'Energy', 'Power Generation'),
            ('POWERGRID', 'Energy', 'Power Transmission'),
            
            # Automobile
            ('MARUTI', 'Automobile', 'Passenger Vehicles'),
            ('TATAMOTORS', 'Automobile', 'Commercial Vehicles'),
            ('M&M', 'Automobile', 'Utility Vehicles'),
            ('BAJAJ-AUTO', 'Automobile', 'Two Wheelers'),
            ('EICHERMOT', 'Automobile', 'Two Wheelers'),
            
            # FMCG
            ('HINDUNILVR', 'FMCG', 'Personal Care'),
            ('ITC', 'FMCG', 'Tobacco & FMCG'),
            ('NESTLEIND', 'FMCG', 'Foods'),
            ('BRITANNIA', 'FMCG', 'Biscuits'),
            
            # Pharma
            ('SUNPHARMA', 'Pharmaceuticals', 'Drugs & Pharma'),
            ('DRREDDY', 'Pharmaceuticals', 'Drugs & Pharma'),
            ('CIPLA', 'Pharmaceuticals', 'Drugs & Pharma'),
            ('DIVISLAB', 'Pharmaceuticals', 'Drugs & Pharma'),
        ]
        
        for symbol, sector, industry in sector_mappings:
            self.cursor.execute("""
            UPDATE instruments_tier1
            SET sector = ?, industry = ?
            WHERE symbol = ?
            """, (sector, industry, symbol))
        
        self.stats['sector_updated'] = self.cursor.rowcount
        self.conn.commit()
        
        logger.info(f"✅ Updated sector/industry for {self.stats['sector_updated']} stocks")
        logger.info("\n   📚 For complete sector data:")
        logger.info("      1. Scrape NSE sector list: https://www.nseindia.com/market-data/")
        logger.info("      2. Use Yahoo Finance API (yfinance library)")
        logger.info("      3. Load from BSE corporate database")
    
    def print_summary(self):
        """Print enrichment summary"""
        logger.info("\n" + "=" * 70)
        logger.info("INDEX LABELING & ENRICHMENT SUMMARY")
        logger.info("=" * 70)
        logger.info(f"F&O availability marked:  {self.stats['fno_marked']:,}")
        logger.info(f"NIFTY 50 marked:          {self.stats['nifty50_marked']:,}")
        logger.info(f"NIFTY 100 marked:         {self.stats['nifty100_marked']:,}")
        logger.info(f"NIFTY 200 marked:         {self.stats['nifty200_marked']:,}")
        logger.info(f"NIFTY 500 marked:         {self.stats['nifty500_marked']:,}")
        logger.info(f"Sector/Industry updated:  {self.stats['sector_updated']:,}")
        logger.info("=" * 70)
        
        # Sample enriched stocks
        logger.info("\nSample enriched stocks (NIFTY 50 with F&O):")
        self.cursor.execute("""
        SELECT symbol, sector, industry, 
               CASE WHEN has_fno = 1 THEN '✅' ELSE '❌' END as fno,
               CASE WHEN is_nifty50 = 1 THEN '✅' ELSE '❌' END as nifty50
        FROM instruments_tier1
        WHERE is_nifty50 = 1 OR has_fno = 1
        ORDER BY symbol
        LIMIT 15
        """)
        
        logger.info(f"\n{'Symbol':<15} {'Sector':<20} {'Industry':<25} F&O N50")
        logger.info("-" * 70)
        for row in self.cursor.fetchall():
            logger.info(f"{row[0]:<15} {(row[1] or '-'):<20} {(row[2] or '-'):<25} {row[3]:^3} {row[4]:^3}")
    
    def run_full_enrichment(self):
        """Execute full enrichment workflow"""
        logger.info("=" * 70)
        logger.info("INDEX LABELING & ENRICHMENT UTILITY")
        logger.info("=" * 70)
        logger.info("")
        
        try:
            # Step 1: Mark F&O availability (always works - cross-references derivatives)
            self.mark_fno_availability()
            
            # Step 2: Mark index membership (try from constituents table first)
            self.mark_index_membership_from_constituents()
            
            # Step 3: Fallback to manual NIFTY50 if constituents not available
            if self.stats['nifty50_marked'] == 0:
                self.manual_mark_nifty50()
            
            # Step 4: Update sector/industry (manual sample for now)
            self.update_sector_industry_manual()
            
            # Summary
            self.print_summary()
            
            logger.info("\n✅ Enrichment completed successfully!")
            logger.info("\nNext steps for production:")
            logger.info("  1. Implement NSE index scraper for NIFTY100/200/500")
            logger.info("  2. Add sector/industry from NSE/BSE/Yahoo Finance")
            logger.info("  3. Schedule daily refresh with DataSyncManager")
            logger.info("  4. Build frontend filters using these labels")
            
        except Exception as e:
            logger.error(f"❌ Enrichment failed: {e}")
            import traceback
            traceback.print_exc()
            self.conn.rollback()
        
        finally:
            self.conn.close()


def main():
    """CLI entry point"""
    utility = IndexLabelingUtility()
    utility.run_full_enrichment()


if __name__ == "__main__":
    main()
