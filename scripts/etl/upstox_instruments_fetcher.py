#!/usr/bin/env python3
"""
Upstox Instruments Fetcher
Downloads complete instruments master from Upstox and populates database
Fetches ALL instrument types including SME, Gold, ETFs, Derivatives, etc.
"""

import requests
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "market_data.db"
UPSTOX_INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json"

# Configuration: FETCH EVERYTHING
FETCH_ALL = True  # User wants all instruments


class UpstoxInstrumentsFetcher:
    """Fetch and classify Upstox instruments"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.stats = {
            "total_downloaded": 0,
            "nse_eq": 0,
            "bse_eq": 0,
            "nse_fo": 0,
            "indices": 0,
            "commodities": 0,
            "currency": 0,
            "others": 0,
            "errors": 0,
            "linked_to_indices": 0
        }
        self.category_counts = {}
    
    def fetch_instruments(self) -> List[Dict]:
        """Download complete instruments file from Upstox"""
        try:
            logger.info(f"Downloading ALL instruments from Upstox...")
            
            # Try CSV format (more reliable)
            csv_url = "https://assets.upstox.com/market-quote/instruments/exchange/complete.csv.gz"
            
            logger.info(f"URL: {csv_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': '*/*',
            }
            
            response = requests.get(csv_url, headers=headers, timeout=60)
            response.raise_for_status()
            
            # Decompress gzip
            import gzip
            import io
            import csv
            
            content = gzip.decompress(response.content).decode('utf-8')
            
            # Parse CSV
            reader = csv.DictReader(io.StringIO(content))
            instruments = []
            
            for row in reader:
                # Convert CSV row to dict matching expected format
                inst = {
                    'instrument_key': row.get('instrument_key', ''),
                    'exchange': row.get('exchange', ''),
                    'tradingsymbol': row.get('tradingsymbol', ''),
                    'symbol': row.get('name', ''),  # CSV has 'name' field
                    'name': row.get('name', ''),
                    'segment': row.get('exchange_segment', ''),
                    'instrument_type': row.get('instrument_type', ''),
                    'isin': row.get('isin', ''),
                    'lot_size': int(row.get('lot_size', 1)) if row.get('lot_size') else 1,
                    'tick_size': float(row.get('tick_size', 0.05)) if row.get('tick_size') else 0.05,
                }
                instruments.append(inst)
            
            self.stats["total_downloaded"] = len(instruments)
            
            logger.info(f"✅ Downloaded {len(instruments):,} instruments")
            return instruments
            
        except Exception as e:
            logger.error(f"❌ Error downloading instruments: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def insert_instruments(self, instruments: List[Dict]):
        """Insert ALL instruments into database"""
        logger.info("\nInserting ALL instruments into database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for inst in instruments:
            try:
                # Extract fields
                instrument_key = inst.get('instrument_key', '')
                exchange = inst.get('exchange', '')
                segment = inst.get('segment', '')
                instrument_type = inst.get('instrument_type', '')
                symbol = inst.get('symbol', '')
                trading_symbol = inst.get('tradingsymbol', '')
                name = inst.get('name', symbol)
                isin = inst.get('isin', '')
                lot_size = inst.get('lot_size', 1)
                tick_size = inst.get('tick_size', 0.05)
                
                # Skip if missing critical fields
                if not instrument_key or not symbol:
                    continue
                
                # Insert everything
                cursor.execute("""
                    INSERT OR REPLACE INTO instruments (
                        instrument_key, symbol, trading_symbol, company_name,
                        exchange, segment, instrument_type, isin,
                        lot_size, tick_size, is_active, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (
                    instrument_key, symbol, trading_symbol, name,
                    exchange, segment, instrument_type, isin,
                    lot_size, tick_size, datetime.now()
                ))
                
                # Track stats by segment
                if segment == 'NSE_EQ':
                    self.stats['nse_eq'] += 1
                elif segment == 'BSE_EQ':
                    self.stats['bse_eq'] += 1
                elif segment == 'NSE_FO':
                    self.stats['nse_fo'] += 1
                elif 'INDEX' in segment:
                    self.stats['indices'] += 1
                elif segment in ['MCX_FO', 'BCD_FO']:
                    self.stats['commodities'] += 1
                elif segment in ['NSE_CD', 'BSE_CD']:
                    self.stats['currency'] += 1
                else:
                    self.stats['others'] += 1
                
                # Track by segment-type combination
                key = f"{segment}|{instrument_type}"
                self.category_counts[key] = self.category_counts.get(key, 0) + 1
                
            except Exception as e:
                logger.error(f"Error inserting {inst.get('symbol', 'UNKNOWN')}: {e}")
                self.stats['errors'] += 1
        
        conn.commit()
        conn.close()
        
        logger.info("✅ All instruments inserted")
    
    def link_to_index_constituents(self):
        """Link instruments to existing index constituents"""
        logger.info("\nLinking instruments to index constituents...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count how many index constituents have matching instruments
        cursor.execute("""
            SELECT COUNT(DISTINCT ic.symbol)
            FROM index_constituents ic
            JOIN instruments i ON ic.symbol = i.symbol
            WHERE ic.is_active = 1 AND i.segment = 'NSE_EQ'
        """)
        
        linked_count = cursor.fetchone()[0]
        self.stats['linked_to_indices'] = linked_count
        
        # Get unlinked symbols
        cursor.execute("""
            SELECT DISTINCT ic.symbol
            FROM index_constituents ic
            LEFT JOIN instruments i ON ic.symbol = i.symbol AND i.segment = 'NSE_EQ'
            WHERE ic.is_active = 1 AND i.symbol IS NULL
        """)
        
        unlinked = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        if unlinked:
            logger.warning(f"⚠️  {len(unlinked)} index constituents not found in NSE_EQ:")
            for sym in unlinked[:10]:  # Show first 10
                logger.warning(f"   - {sym}")
            if len(unlinked) > 10:
                logger.warning(f"   ... and {len(unlinked) - 10} more")
        else:
            logger.info("✅ All index constituents linked to instruments!")
    
    def print_summary(self):
        """Print execution summary"""
        logger.info("\n" + "=" * 70)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total downloaded:       {self.stats['total_downloaded']:,}")
        logger.info(f"NSE_EQ inserted:        {self.stats['nse_eq']:,}")
        logger.info(f"BSE_EQ inserted:        {self.stats['bse_eq']:,}")
        logger.info(f"NSE_FO inserted:        {self.stats['nse_fo']:,}")
        logger.info(f"Indices inserted:       {self.stats['indices']:,}")
        logger.info(f"Commodities inserted:   {self.stats['commodities']:,}")
        logger.info(f"Currency inserted:      {self.stats['currency']:,}")
        logger.info(f"Others inserted:        {self.stats['others']:,}")
        logger.info(f"Errors:                 {self.stats['errors']:,}")
        logger.info(f"Linked to indices:      {self.stats['linked_to_indices']:,}")
        logger.info("=" * 70)
        
        # Database statistics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        logger.info("\nTOP 20 CATEGORIES (Segment|Type):")
        logger.info("-" * 70)
        
        # Sort by count
        sorted_cats = sorted(self.category_counts.items(), key=lambda x: x[1], reverse=True)
        for cat, count in sorted_cats[:20]:
            logger.info(f"  {cat:30} | {count:,}")
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM instruments WHERE is_active = 1")
        total_instruments = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM instruments WHERE is_active = 1")
        unique_symbols = cursor.fetchone()[0]
        
        logger.info(f"\nTotal active instruments: {total_instruments:,}")
        logger.info(f"Unique symbols:           {unique_symbols:,}")
        
        # Nifty 50 verification
        cursor.execute("""
            SELECT COUNT(*)
            FROM index_constituents ic
            JOIN instruments i ON ic.symbol = i.symbol
            WHERE ic.index_code = 'NIFTY50' AND ic.is_active = 1 AND i.segment = 'NSE_EQ'
        """)
        nifty50_linked = cursor.fetchone()[0]
        logger.info(f"Nifty 50 stocks linked:   {nifty50_linked}/51")
        
        # Sample NSE_EQ stocks
        logger.info("\nSample NSE_EQ Stocks:")
        cursor.execute("""
            SELECT symbol, trading_symbol, instrument_type, company_name
            FROM instruments
            WHERE segment = 'NSE_EQ'
            ORDER BY symbol
            LIMIT 10
        """)
        for row in cursor.fetchall():
            logger.info(f"  {row[0]:15} | {row[1]:20} | {row[2]:5} | {row[3][:40]}")
        
        conn.close()
        logger.info("=" * 70)
    
    def run(self):
        """Main execution"""
        logger.info("=" * 70)
        logger.info("UPSTOX INSTRUMENTS FETCHER - FETCH ALL MODE")
        logger.info("=" * 70)
        logger.info(f"\nConfiguration: FETCH_ALL = {FETCH_ALL}")
        logger.info("This will fetch ALL 207K+ instruments including:")
        logger.info("  ✅ NSE_EQ (EQ, BE, SM, SG, N1, BZ)")
        logger.info("  ✅ BSE_EQ (A, B, X, XT, M, T, Z, P, F, G)")
        logger.info("  ✅ NSE_FO (CE, PE, FUT)")
        logger.info("  ✅ Indices, Commodities, Currency")
        logger.info("")
        
        # Step 1: Download
        instruments = self.fetch_instruments()
        if not instruments:
            logger.error("Failed to download instruments")
            return False
        
        # Step 2: Insert all
        self.insert_instruments(instruments)
        
        # Step 3: Link to index constituents
        self.link_to_index_constituents()
        
        # Step 4: Summary
        self.print_summary()
        
        logger.info("\n✅ Upstox instruments fetch completed!")
        return True


def main():
    """Main execution"""
    fetcher = UpstoxInstrumentsFetcher()
    success = fetcher.run()
    
    if success:
        logger.info("\nNext steps:")
        logger.info("  1. Test movers service")
        logger.info("  2. Verify Market Explorer page")
        logger.info("  3. Check instrument browser")
    else:
        logger.error("\n❌ Fetch failed - check errors above")


if __name__ == "__main__":
    main()
