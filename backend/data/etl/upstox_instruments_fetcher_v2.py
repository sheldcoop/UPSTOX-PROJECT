#!/usr/bin/env python3
"""
Upstox Instruments Fetcher V2 - Production Grade
Replaces deprecated CSV with JSON format, implements tiered filtering
Designed for daily automated sync at 6:30 AM IST
"""

import gzip
import json
import requests
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Tuple
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "market_data.db"
UPSTOX_CDN_BASE = "https://assets.upstox.com/market-quote/instruments/exchange/"


class UpstoxInstrumentsFetcherV2:
    """
    Production-grade tiered instruments fetcher
    - Uses JSON format (CSV deprecated)
    - Filters into 4 tiers: Tier1 (liquid equity), SME, Derivatives, Indices/ETFs
    - Auto-cleanup expired derivatives
    - Future-proof schema with sector, F&O, index membership columns
    """
    
    # Tier configuration matching MARKET_INSTRUMENTS_GUIDE.md
    TIER_CONFIG = {
        'tier1': {
            'description': 'Liquid Equity (NSE EQ + BSE A/B/XT)',
            'filters': {
                'NSE': {
                    'segments': ['NSE_EQ'],
                    'instrument_types': ['EQ']
                },
                'BSE': {
                    'segments': ['BSE_EQ'],
                    'instrument_types': ['A', 'B', 'XT']
                }
            },
            'table': 'instruments_tier1',
            'expected_count': 5664
        },
        'sme': {
            'description': 'SME Stocks (NSE SM + BSE M)',
            'filters': {
                'NSE': {
                    'segments': ['NSE_EQ'],
                    'instrument_types': ['SM']
                },
                'BSE': {
                    'segments': ['BSE_EQ'],
                    'instrument_types': ['M']
                }
            },
            'table': 'instruments_sme',
            'expected_count': 814
        },
        'derivatives': {
            'description': 'F&O Contracts (Options + Futures)',
            'filters': {
                'instrument_types': ['OPTIDX', 'OPTSTK', 'FUTIDX', 'FUTSTK', 
                                    'FUTCOM', 'FUTCUR', 'OPTCUR', 'OPTIRD']
            },
            'table': 'instruments_derivatives',
            'expected_count': 186201
        },
        'indices_etfs': {
            'description': 'Indices & ETFs',
            'filters': {
                'instrument_types': ['INDEX', 'IDX'],
                'etf_segments': ['NSE_EQ'],
                'etf_types': ['N1']  # ETFs on NSE
            },
            'table': 'instruments_indices_etfs',
            'expected_count': 312
        }
    }
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        
        # Statistics tracking
        self.stats = {
            'total_fetched': 0,
            'tier1_inserted': 0,
            'sme_inserted': 0,
            'derivatives_inserted': 0,
            'indices_inserted': 0,
            'errors': 0,
            'expired_cleaned': 0
        }
        
        self.start_time = time.time()
    
    def fetch_complete_json(self) -> List[Dict]:
        """Download complete.json.gz from Upstox CDN (replaces CSV)"""
        url = f"{UPSTOX_CDN_BASE}complete.json.gz"
        
        logger.info(f"📥 Downloading instruments from {url}")
        logger.info("   Format: JSON (CSV is deprecated)")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip'
            }
            
            response = requests.get(url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()
            
            # Decompress gzip
            with gzip.GzipFile(fileobj=response.raw) as f:
                data = json.load(f)
            
            self.stats['total_fetched'] = len(data)
            logger.info(f"✅ Downloaded {len(data):,} instruments (JSON format)")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error downloading instruments: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def filter_tier1(self, instruments: List[Dict]) -> List[Dict]:
        """
        Extract Tier 1: Liquid Equity (NSE EQ + BSE A/B/XT)
        Expected: ~5,664 instruments
        """
        filtered = []
        config = self.TIER_CONFIG['tier1']['filters']
        
        for inst in instruments:
            exchange = inst.get('exchange')
            segment = inst.get('segment')
            inst_type = inst.get('instrument_type')
            
            # NSE EQ filter
            if exchange == 'NSE' and segment in config['NSE']['segments']:
                if inst_type in config['NSE']['instrument_types']:
                    filtered.append(self._parse_tier1_instrument(inst))
            
            # BSE A/B/XT filter
            elif exchange == 'BSE' and segment in config['BSE']['segments']:
                if inst_type in config['BSE']['instrument_types']:
                    filtered.append(self._parse_tier1_instrument(inst))
        
        logger.info(f"✅ Tier 1 filtered: {len(filtered):,} liquid equity instruments")
        return filtered
    
    def _parse_tier1_instrument(self, inst: Dict) -> Dict:
        """Parse JSON fields for Tier 1 schema"""
        return {
            'instrument_key': inst.get('instrument_key'),
            'exchange': inst.get('exchange'),
            'segment': inst.get('segment'),
            'instrument_type': inst.get('instrument_type'),
            'symbol': inst.get('name', ''),  # Company name in 'name' field
            'trading_symbol': inst.get('trading_symbol', ''),
            'company_name': inst.get('name', ''),
            'isin': inst.get('isin', ''),
            'lot_size': inst.get('lot_size', 1),
            'tick_size': inst.get('tick_size', 0.05),
            'freeze_quantity': inst.get('freeze_quantity', 0),
            
            # Future-proof columns (to be populated later)
            'sector': None,
            'industry': None,
            'has_fno': 0,  # Will be marked by post-processing
            'fno_segment': None,
            'index_memberships': None,
            'is_nifty50': 0,
            'is_nifty100': 0,
            'is_nifty200': 0,
            'is_nifty500': 0,
            'market_cap_category': None,
            'avg_daily_volume': None,
            
            'is_active': 1,
            'last_updated': datetime.now()
        }
    
    def filter_sme(self, instruments: List[Dict]) -> List[Dict]:
        """
        Extract SME stocks with risk flags (NSE SM + BSE M)
        Expected: ~814 instruments
        """
        filtered = []
        config = self.TIER_CONFIG['sme']['filters']
        
        for inst in instruments:
            exchange = inst.get('exchange')
            segment = inst.get('segment')
            inst_type = inst.get('instrument_type')
            
            # NSE SME filter
            if exchange == 'NSE' and segment in config['NSE']['segments']:
                if inst_type in config['NSE']['instrument_types']:
                    filtered.append(self._parse_sme_instrument(inst))
            
            # BSE SME filter
            elif exchange == 'BSE' and segment in config['BSE']['segments']:
                if inst_type in config['BSE']['instrument_types']:
                    filtered.append(self._parse_sme_instrument(inst))
        
        logger.info(f"⚠️  SME filtered: {len(filtered):,} high-risk instruments")
        return filtered
    
    def _parse_sme_instrument(self, inst: Dict) -> Dict:
        """Parse JSON fields for SME schema with risk flags"""
        lot_size = inst.get('lot_size', 1)
        
        return {
            'instrument_key': inst.get('instrument_key'),
            'exchange': inst.get('exchange'),
            'segment': inst.get('segment'),
            'instrument_type': inst.get('instrument_type'),
            'symbol': inst.get('name', ''),
            'trading_symbol': inst.get('trading_symbol', ''),
            'company_name': inst.get('name', ''),
            'isin': inst.get('isin', ''),
            'lot_size': lot_size,
            'tick_size': inst.get('tick_size', 0.05),
            'freeze_quantity': inst.get('freeze_quantity', 0),
            
            # Auto risk flags
            'risk_level': 'VERY_HIGH' if lot_size > 5000 else 'HIGH',
            'min_lot_warning': 1 if lot_size > 1000 else 0,
            'liquidity_tier': 'VERY_LOW' if lot_size > 5000 else 'LOW',
            
            # Future-proof
            'sector': None,
            'industry': None,
            'listing_date': None,
            'is_graded': 0,
            'sme_grade': None,
            
            'is_active': 1,
            'last_updated': datetime.now()
        }
    
    def filter_derivatives(self, instruments: List[Dict]) -> List[Dict]:
        """
        Extract derivatives (F&O) with expiry tracking
        Expected: ~186,201 instruments
        """
        filtered = []
        config = self.TIER_CONFIG['derivatives']['filters']
        
        for inst in instruments:
            inst_type = inst.get('instrument_type')
            
            if inst_type in config['instrument_types']:
                filtered.append(self._parse_derivative_instrument(inst))
        
        logger.info(f"✅ Derivatives filtered: {len(filtered):,} F&O contracts")
        return filtered
    
    def _parse_derivative_instrument(self, inst: Dict) -> Dict:
        """Parse JSON fields for derivatives schema"""
        # Handle expiry (milliseconds timestamp to date)
        expiry_ms = inst.get('expiry')
        if expiry_ms:
            expiry = date.fromtimestamp(expiry_ms / 1000)
        else:
            expiry = None
        
        strike = inst.get('strike', 0.0) or inst.get('strike_price', 0.0)
        
        # Determine option type
        inst_type = inst.get('instrument_type')
        if inst_type in ['OPTIDX', 'OPTSTK', 'OPTCUR', 'OPTIRD']:
            # Options have CE/PE suffix in trading_symbol
            trading_sym = inst.get('trading_symbol', '')
            if 'CE' in trading_sym or inst_type.endswith('CE'):
                option_type = 'CE'
            elif 'PE' in trading_sym or inst_type.endswith('PE'):
                option_type = 'PE'
            else:
                option_type = None
        else:
            option_type = 'FUT'  # Futures
        
        return {
            'instrument_key': inst.get('instrument_key'),
            'exchange': inst.get('exchange'),
            'segment': inst.get('segment'),
            'instrument_type': inst_type,
            'symbol': inst.get('name', ''),
            'trading_symbol': inst.get('trading_symbol', ''),
            
            # Underlying linking
            'underlying_key': inst.get('underlying_key', ''),
            'underlying_symbol': inst.get('underlying_symbol', ''),
            'underlying_type': inst.get('underlying_type', ''),
            
            # Contract specs
            'expiry': expiry,
            'strike_price': strike,
            'option_type': option_type,
            
            # Trading specs
            'lot_size': inst.get('lot_size', 1),
            'tick_size': inst.get('tick_size', 0.05),
            'freeze_quantity': inst.get('freeze_quantity', 0),
            'minimum_lot': inst.get('minimum_lot', inst.get('lot_size', 1)),
            
            # Contract metadata
            'weekly': inst.get('weekly', False),
            'is_atm': 0,  # To be calculated
            'moneyness': None,
            
            # Greeks (to be populated later)
            'implied_volatility': None,
            'delta': None,
            'gamma': None,
            'theta': None,
            'vega': None,
            
            'is_active': 1,
            'is_expired': 0,
            'last_updated': datetime.now()
        }
    
    def filter_indices_etfs(self, instruments: List[Dict]) -> List[Dict]:
        """
        Extract indices and ETFs
        Expected: ~312 instruments
        """
        filtered = []
        config = self.TIER_CONFIG['indices_etfs']['filters']
        
        for inst in instruments:
            inst_type = inst.get('instrument_type')
            segment = inst.get('segment')
            
            # Indices
            if inst_type in config['instrument_types']:
                filtered.append(self._parse_index_instrument(inst, is_etf=False))
            
            # ETFs (N1 type on NSE_EQ)
            elif segment in config['etf_segments'] and inst_type in config['etf_types']:
                filtered.append(self._parse_index_instrument(inst, is_etf=True))
        
        logger.info(f"✅ Indices/ETFs filtered: {len(filtered):,} instruments")
        return filtered
    
    def _parse_index_instrument(self, inst: Dict, is_etf: bool) -> Dict:
        """Parse JSON fields for indices/ETFs schema"""
        return {
            'instrument_key': inst.get('instrument_key'),
            'exchange': inst.get('exchange'),
            'segment': inst.get('segment'),
            'instrument_type': inst.get('instrument_type'),
            'symbol': inst.get('name', ''),
            'trading_symbol': inst.get('trading_symbol', ''),
            'name': inst.get('name', ''),
            
            # Index metadata (to be populated later)
            'index_code': None,
            'constituent_count': None,
            'base_value': None,
            'base_date': None,
            
            # ETF metadata
            'is_etf': 1 if is_etf else 0,
            'underlying_index': None,
            'aum': None,
            'expense_ratio': None,
            
            'is_active': 1,
            'last_updated': datetime.now()
        }
    
    def bulk_insert_tier1(self, data: List[Dict]):
        """Bulk insert into instruments_tier1"""
        if not data:
            return
        
        columns = list(data[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        col_names = ', '.join(columns)
        
        query = f"""
        INSERT OR REPLACE INTO instruments_tier1 ({col_names})
        VALUES ({placeholders})
        """
        
        self.cursor.executemany(query, [tuple(d.values()) for d in data])
        self.stats['tier1_inserted'] = len(data)
        logger.info(f"💾 Inserted {len(data):,} instruments into tier1")
    
    def bulk_insert_sme(self, data: List[Dict]):
        """Bulk insert into instruments_sme"""
        if not data:
            return
        
        columns = list(data[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        col_names = ', '.join(columns)
        
        query = f"""
        INSERT OR REPLACE INTO instruments_sme ({col_names})
        VALUES ({placeholders})
        """
        
        self.cursor.executemany(query, [tuple(d.values()) for d in data])
        self.stats['sme_inserted'] = len(data)
        logger.info(f"💾 Inserted {len(data):,} instruments into SME table")
    
    def bulk_insert_derivatives(self, data: List[Dict]):
        """Bulk insert into instruments_derivatives"""
        if not data:
            return
        
        columns = list(data[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        col_names = ', '.join(columns)
        
        query = f"""
        INSERT OR REPLACE INTO instruments_derivatives ({col_names})
        VALUES ({placeholders})
        """
        
        self.cursor.executemany(query, [tuple(d.values()) for d in data])
        self.stats['derivatives_inserted'] = len(data)
        logger.info(f"💾 Inserted {len(data):,} derivatives")
    
    def bulk_insert_indices_etfs(self, data: List[Dict]):
        """Bulk insert into instruments_indices_etfs"""
        if not data:
            return
        
        columns = list(data[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        col_names = ', '.join(columns)
        
        query = f"""
        INSERT OR REPLACE INTO instruments_indices_etfs ({col_names})
        VALUES ({placeholders})
        """
        
        self.cursor.executemany(query, [tuple(d.values()) for d in data])
        self.stats['indices_inserted'] = len(data)
        logger.info(f"💾 Inserted {len(data):,} indices/ETFs")
    
    def cleanup_expired_derivatives(self):
        """Auto-deactivate expired derivatives contracts"""
        today = date.today()
        
        self.cursor.execute("""
        UPDATE instruments_derivatives
        SET is_active = 0, is_expired = 1
        WHERE expiry < ? AND is_active = 1
        """, (today,))
        
        expired_count = self.cursor.rowcount
        self.stats['expired_cleaned'] = expired_count
        
        if expired_count > 0:
            logger.warning(f"⏰ Deactivated {expired_count:,} expired derivatives")
        else:
            logger.info("✅ No expired derivatives found")
    
    def mark_fno_availability(self):
        """
        Mark tier1 stocks that have F&O availability
        Cross-reference with derivatives table
        """
        logger.info("🔗 Marking F&O availability in tier1...")
        
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
            WHERE underlying_type = 'EQUITY'
        )
        """)
        
        fno_marked = self.cursor.rowcount
        logger.info(f"✅ Marked {fno_marked} tier1 stocks with F&O availability")
    
    def log_sync_stats(self):
        """Log sync statistics to instruments_sync_log"""
        duration = time.time() - self.start_time
        
        status = 'SUCCESS'
        if self.stats['errors'] > 0:
            status = 'PARTIAL' if self.stats['tier1_inserted'] > 0 else 'FAILED'
        
        self.cursor.execute("""
        INSERT INTO instruments_sync_log 
        (sync_type, instruments_fetched, instruments_inserted, 
         instruments_updated, instruments_deactivated, 
         duration_seconds, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'full',
            self.stats['total_fetched'],
            self.stats['tier1_inserted'] + self.stats['sme_inserted'] + 
            self.stats['derivatives_inserted'] + self.stats['indices_inserted'],
            0,  # Updated count (we use INSERT OR REPLACE)
            self.stats['expired_cleaned'],
            round(duration, 2),
            status,
            None
        ))
    
    def print_summary(self):
        """Print execution summary"""
        duration = time.time() - self.start_time
        
        logger.info("\n" + "=" * 70)
        logger.info("TIERED INSTRUMENTS SYNC SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total fetched:          {self.stats['total_fetched']:,}")
        logger.info(f"Tier 1 inserted:        {self.stats['tier1_inserted']:,}")
        logger.info(f"SME inserted:           {self.stats['sme_inserted']:,}")
        logger.info(f"Derivatives inserted:   {self.stats['derivatives_inserted']:,}")
        logger.info(f"Indices/ETFs inserted:  {self.stats['indices_inserted']:,}")
        logger.info(f"Expired cleaned:        {self.stats['expired_cleaned']:,}")
        logger.info(f"Errors:                 {self.stats['errors']:,}")
        logger.info(f"Duration:               {duration:.2f}s")
        logger.info("=" * 70)
        
        # Verify against expected counts
        config = self.TIER_CONFIG
        logger.info("\nExpected vs Actual:")
        logger.info(f"Tier 1:      Expected ~{config['tier1']['expected_count']:,}, Got {self.stats['tier1_inserted']:,}")
        logger.info(f"SME:         Expected ~{config['sme']['expected_count']:,}, Got {self.stats['sme_inserted']:,}")
        logger.info(f"Derivatives: Expected ~{config['derivatives']['expected_count']:,}, Got {self.stats['derivatives_inserted']:,}")
        logger.info("=" * 70)
    
    def run_full_sync(self):
        """Execute complete tiered sync (called by DataSyncManager)"""
        logger.info("=" * 70)
        logger.info("UPSTOX INSTRUMENTS FETCHER V2 - TIERED SYNC")
        logger.info("=" * 70)
        logger.info("Format: JSON (CSV deprecated)")
        logger.info("Mode:   Tiered filtering (Tier1, SME, Derivatives, Indices)")
        logger.info("")
        
        try:
            # Step 1: Download JSON
            all_instruments = self.fetch_complete_json()
            
            # Step 2: Filter by tier
            logger.info("\n📊 Filtering instruments by tier...")
            tier1_data = self.filter_tier1(all_instruments)
            sme_data = self.filter_sme(all_instruments)
            derivatives_data = self.filter_derivatives(all_instruments)
            indices_data = self.filter_indices_etfs(all_instruments)
            
            # Step 3: Bulk insert
            logger.info("\n💾 Inserting into database...")
            self.bulk_insert_tier1(tier1_data)
            self.bulk_insert_sme(sme_data)
            self.bulk_insert_derivatives(derivatives_data)
            self.bulk_insert_indices_etfs(indices_data)
            
            # Step 4: Post-processing
            logger.info("\n🔧 Post-processing...")
            self.cleanup_expired_derivatives()
            self.mark_fno_availability()
            
            # Step 5: Commit & log
            self.conn.commit()
            self.log_sync_stats()
            
            # Step 6: Summary
            self.print_summary()
            
            logger.info("\n✅ Tiered instruments sync completed successfully!")
            logger.info("\nNext steps:")
            logger.info("  1. Run index_labeling_script.py to mark NIFTY50/100/200")
            logger.info("  2. Add sector/industry data from external sources")
            logger.info("  3. Configure DataSyncManager for daily 6:30 AM automation")
            
            return True
            
        except Exception as e:
            logger.error(f"\n❌ Sync failed: {e}")
            import traceback
            traceback.print_exc()
            self.conn.rollback()
            
            self.stats['errors'] = 1
            self.log_sync_stats()
            self.conn.commit()
            
            return False
        
        finally:
            self.conn.close()


def main():
    """CLI entry point"""
    fetcher = UpstoxInstrumentsFetcherV2()
    success = fetcher.run_full_sync()
    
    if not success:
        exit(1)


if __name__ == "__main__":
    main()
