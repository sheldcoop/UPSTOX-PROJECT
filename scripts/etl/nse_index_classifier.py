#!/usr/bin/env python3
"""
NSE Index Classifier
Maps scraped NSE index constituents to instruments_tier1 table
Updates index membership flags and populates index_constituents_v2
"""

import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "market_data.db"
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "nse_indices"


class NSEIndexClassifier:
    """
    Classifies instruments based on NSE index membership
    - Matches symbols/ISINs to instruments_tier1
    - Updates index membership flags (is_nifty50, is_nifty100, etc.)
    - Populates index_constituents_v2 with detailed mappings
    - Adds sector/industry metadata from scraped data
    """
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        self.stats = {
            'indices_processed': 0,
            'constituents_found': 0,
            'constituents_matched': 0,
            'tier1_updated': 0,
            'mappings_created': 0,
            'sectors_added': 0,
            'unmatched_symbols': []
        }
        
        # Cache for instrument lookups
        self.instrument_cache: Dict[str, str] = {}  # symbol -> instrument_key
        self._build_instrument_cache()
    
    def _build_instrument_cache(self):
        """Build cache of symbol -> instrument_key mappings"""
        logger.info("📦 Building instrument cache...")
        
        self.cursor.execute("""
        SELECT symbol, instrument_key, isin 
        FROM instruments_tier1 
        WHERE exchange = 'NSE' AND is_active = 1
        """)
        
        for symbol, instrument_key, isin in self.cursor.fetchall():
            self.instrument_cache[symbol] = instrument_key
            # Also cache by ISIN for better matching
            if isin:
                self.instrument_cache[f"ISIN:{isin}"] = instrument_key
        
        logger.info(f"✅ Cached {len(self.instrument_cache)} instruments")
    
    def load_enriched_data(self, index_code: str) -> Optional[pd.DataFrame]:
        """Load enriched CSV from scraper output"""
        csv_path = DATA_DIR / f"{index_code}_enriched.csv"
        
        if not csv_path.exists():
            logger.warning(f"⚠️  No enriched data found for {index_code}: {csv_path}")
            return None
        
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"📄 Loaded {len(df)} constituents for {index_code}")
            return df
        except Exception as e:
            logger.error(f"❌ Failed to load {csv_path}: {e}")
            return None
    
    def match_to_instruments(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Match constituent symbols to instruments_tier1
        Returns DataFrame with added instrument_key column
        """
        instrument_keys = []
        unmatched = []
        
        for idx, row in df.iterrows():
            symbol = row.get('symbol', '').strip()
            isin = row.get('isin', '').strip()
            
            # Try matching by symbol first
            instrument_key = self.instrument_cache.get(symbol)
            
            # Fallback to ISIN matching
            if not instrument_key and isin:
                instrument_key = self.instrument_cache.get(f"ISIN:{isin}")
            
            if instrument_key:
                instrument_keys.append(instrument_key)
                self.stats['constituents_matched'] += 1
            else:
                instrument_keys.append(None)
                unmatched.append(symbol)
                self.stats['unmatched_symbols'].append(symbol)
        
        df['instrument_key'] = instrument_keys
        
        if unmatched:
            logger.warning(f"⚠️  {len(unmatched)} symbols not matched: {unmatched[:10]}")
        
        return df
    
    def populate_constituents_table(self, index_code: str, df: pd.DataFrame):
        """Populate index_constituents_v2 with constituent mappings"""
        logger.info(f"💾 Populating index_constituents_v2 for {index_code}...")
        
        # Filter matched constituents
        matched_df = df[df['instrument_key'].notna()].copy()
        
        if matched_df.empty:
            logger.warning(f"⚠️  No matched constituents for {index_code}")
            return
        
        # Prepare data for insertion
        records = []
        for _, row in matched_df.iterrows():
            records.append((
                index_code,
                row['instrument_key'],
                row.get('symbol', ''),
                row.get('company_name', ''),
                row.get('isin', ''),
                row.get('weight', None),
                row.get('sector', None),
                row.get('industry', None),
                datetime.now().date()
            ))
        
        # Bulk insert with conflict handling
        self.cursor.executemany("""
        INSERT OR REPLACE INTO index_constituents_v2 
        (index_code, instrument_key, symbol, company_name, isin, 
         weight, sector, industry, effective_date, is_active, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
        """, records)
        
        self.conn.commit()
        self.stats['mappings_created'] += len(records)
        
        logger.info(f"✅ Inserted {len(records)} constituents")
    
    def update_tier1_flags(self, index_code: str, df: pd.DataFrame):
        """Update boolean flags in instruments_tier1 for quick filtering"""
        logger.info(f"🚩 Updating tier1 flags for {index_code}...")
        
        # Mapping of index codes to column names
        flag_mapping = {
            'NIFTY50': ('is_nifty50', 'weight_nifty50'),
            'NIFTYNEXT50': ('is_niftynext50', None),
            'NIFTY100': ('is_nifty100', 'weight_nifty100'),
            'NIFTY200': ('is_nifty200', None),
            'NIFTY500': ('is_nifty500', 'weight_nifty500'),
            'NIFTYMIDCAP150': ('is_midcap', None),
            'NIFTYMIDCAP100': ('is_midcap', None),
            'NIFTYMIDCAP50': ('is_midcap', None),
            'NIFTYSMALLCAP500': ('is_smallcap', None),
            'NIFTYSMALLCAP250': ('is_smallcap', None),
            'NIFTYSMALLCAP100': ('is_smallcap', None),
        }
        
        if index_code not in flag_mapping:
            logger.debug(f"  ℹ️  No flag mapping for {index_code}, skipping flag update")
            return
        
        flag_col, weight_col = flag_mapping[index_code]
        
        # Get matched instrument keys
        matched_df = df[df['instrument_key'].notna()].copy()
        instrument_keys = matched_df['instrument_key'].tolist()
        
        if not instrument_keys:
            return
        
        # Update flag
        placeholders = ','.join(['?' for _ in instrument_keys])
        self.cursor.execute(f"""
        UPDATE instruments_tier1
        SET {flag_col} = 1, last_updated = datetime('now')
        WHERE instrument_key IN ({placeholders})
        """, instrument_keys)
        
        # Update weight if applicable
        if weight_col and 'weight' in matched_df.columns:
            for _, row in matched_df.iterrows():
                if row['weight'] is not None:
                    self.cursor.execute(f"""
                    UPDATE instruments_tier1
                    SET {weight_col} = ?, last_updated = datetime('now')
                    WHERE instrument_key = ?
                    """, (row['weight'], row['instrument_key']))
        
        self.conn.commit()
        self.stats['tier1_updated'] += len(instrument_keys)
        
        logger.info(f"✅ Updated {len(instrument_keys)} instruments with {flag_col}=1")
    
    def update_index_memberships(self, index_code: str, df: pd.DataFrame):
        """Update comma-separated index_memberships column"""
        logger.info(f"🏷️  Updating index_memberships for {index_code}...")
        
        matched_df = df[df['instrument_key'].notna()].copy()
        
        for instrument_key in matched_df['instrument_key']:
            # Get current memberships
            self.cursor.execute("""
            SELECT index_memberships FROM instruments_tier1
            WHERE instrument_key = ?
            """, (instrument_key,))
            
            result = self.cursor.fetchone()
            if not result:
                continue
            
            current = result[0] or ''
            memberships = set(current.split(',')) if current else set()
            memberships.add(index_code)
            memberships.discard('')  # Remove empty strings
            
            # Update with sorted comma-separated list
            new_memberships = ','.join(sorted(memberships))
            self.cursor.execute("""
            UPDATE instruments_tier1
            SET index_memberships = ?, last_updated = datetime('now')
            WHERE instrument_key = ?
            """, (new_memberships, instrument_key))
        
        self.conn.commit()
        logger.info(f"✅ Updated index_memberships for {len(matched_df)} instruments")
    
    def update_sector_industry(self, df: pd.DataFrame):
        """Update sector/industry metadata from enriched data"""
        logger.info(f"🏭 Updating sector/industry metadata...")
        
        matched_df = df[df['instrument_key'].notna()].copy()
        
        # Check what columns are available
        has_sector = 'sector' in matched_df.columns
        has_industry = 'industry' in matched_df.columns
        
        if not has_sector and not has_industry:
            logger.info("  ℹ️  No sector/industry data to update")
            return
        
        # Filter rows with metadata
        if has_sector and has_industry:
            has_metadata = matched_df[
                matched_df['sector'].notna() | matched_df['industry'].notna()
            ]
        elif has_sector:
            has_metadata = matched_df[matched_df['sector'].notna()]
        else:  # has_industry only
            has_metadata = matched_df[matched_df['industry'].notna()]
        
        if has_metadata.empty:
            logger.info("  ℹ️  No sector/industry data to update")
            return
        
        for _, row in has_metadata.iterrows():
            updates = []
            params = []
            
            if has_sector and pd.notna(row.get('sector')):
                updates.append("sector = ?")
                params.append(row['sector'])
            
            if has_industry and pd.notna(row.get('industry')):
                updates.append("industry = ?")
                params.append(row['industry'])
            
            if updates:
                updates.append("last_updated = datetime('now')")
                params.append(row['instrument_key'])
                
                query = f"""
                UPDATE instruments_tier1
                SET {', '.join(updates)}
                WHERE instrument_key = ?
                """
                self.cursor.execute(query, params)
        
        self.conn.commit()
        self.stats['sectors_added'] += len(has_metadata)
        
        logger.info(f"✅ Updated sector/industry for {len(has_metadata)} instruments")
    
    def classify_index(self, index_code: str):
        """Complete classification workflow for one index"""
        logger.info(f"\n{'=' * 70}")
        logger.info(f"CLASSIFYING: {index_code}")
        logger.info(f"{'=' * 70}")
        
        # Load enriched data
        df = self.load_enriched_data(index_code)
        if df is None:
            logger.error(f"❌ Cannot classify {index_code} - no data found")
            return
        
        self.stats['constituents_found'] += len(df)
        
        # Match to instruments_tier1
        df = self.match_to_instruments(df)
        
        # Populate mappings table
        self.populate_constituents_table(index_code, df)
        
        # Update tier1 flags
        self.update_tier1_flags(index_code, df)
        
        # Update index_memberships
        self.update_index_memberships(index_code, df)
        
        # Update sector/industry
        self.update_sector_industry(df)
        
        self.stats['indices_processed'] += 1
        logger.info(f"✅ {index_code} classification complete")
    
    def get_all_scraped_indices(self) -> List[str]:
        """Get list of indices with enriched CSV files"""
        csv_files = DATA_DIR.glob('*_enriched.csv')
        indices = [f.stem.replace('_enriched', '') for f in csv_files]
        return sorted(indices)
    
    def classify_all_indices(self):
        """Classify all scraped indices"""
        logger.info("=" * 70)
        logger.info("NSE INDEX CLASSIFIER - CLASSIFYING ALL INDICES")
        logger.info("=" * 70)
        
        indices = self.get_all_scraped_indices()
        
        if not indices:
            logger.error("❌ No enriched index data found!")
            logger.info(f"   Expected location: {DATA_DIR}")
            logger.info(f"   Run nse_index_scraper.py first")
            return
        
        logger.info(f"\nFound {len(indices)} indices to classify")
        logger.info("")
        
        for i, index_code in enumerate(indices, 1):
            logger.info(f"\n[{i}/{len(indices)}] Processing {index_code}...")
            self.classify_index(index_code)
        
        self.print_summary()
    
    def print_summary(self):
        """Print classification summary"""
        logger.info("\n" + "=" * 70)
        logger.info("CLASSIFICATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Indices processed:      {self.stats['indices_processed']}")
        logger.info(f"Constituents found:     {self.stats['constituents_found']:,}")
        logger.info(f"Constituents matched:   {self.stats['constituents_matched']:,}")
        logger.info(f"Match rate:             {self.stats['constituents_matched']/max(self.stats['constituents_found'],1)*100:.1f}%")
        logger.info(f"Tier1 updated:          {self.stats['tier1_updated']:,}")
        logger.info(f"Mappings created:       {self.stats['mappings_created']:,}")
        logger.info(f"Sectors added:          {self.stats['sectors_added']:,}")
        
        unmatched_count = len(set(self.stats['unmatched_symbols']))
        logger.info(f"Unmatched symbols:      {unmatched_count}")
        
        if unmatched_count > 0:
            logger.info("\n⚠️  Sample unmatched symbols:")
            for symbol in sorted(set(self.stats['unmatched_symbols']))[:15]:
                logger.info(f"  - {symbol}")
        
        # Database verification
        self.cursor.execute("""
        SELECT COUNT(DISTINCT instrument_key)
        FROM index_constituents_v2
        WHERE is_active = 1
        """)
        total_classified = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
        SELECT COUNT(*)
        FROM instruments_tier1
        WHERE is_nifty50 = 1 OR is_nifty100 = 1 OR is_nifty500 = 1
        """)
        flagged_count = self.cursor.fetchone()[0]
        
        logger.info(f"\n📊 Database status:")
        logger.info(f"  Unique classified instruments: {total_classified:,}")
        logger.info(f"  Instruments with index flags:  {flagged_count:,}")
        
        # Sample classified stocks
        logger.info(f"\n📋 Sample classified stocks (NIFTY 50):")
        self.cursor.execute("""
        SELECT symbol, sector, industry, index_memberships
        FROM instruments_tier1
        WHERE is_nifty50 = 1
        ORDER BY symbol
        LIMIT 10
        """)
        
        for symbol, sector, industry, memberships in self.cursor.fetchall():
            logger.info(f"  {symbol:15} | {sector or '-':20} | {industry or '-':30} | {memberships or '-'}")
        
        logger.info("=" * 70)
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """CLI entry point"""
    classifier = NSEIndexClassifier()
    
    try:
        classifier.classify_all_indices()
        
        logger.info("\n✅ Classification completed successfully!")
        logger.info("\nNext steps:")
        logger.info("  1. Query instruments by index: SELECT * FROM instruments_tier1 WHERE is_nifty50 = 1")
        logger.info("  2. Filter by sector: SELECT * FROM instruments_tier1 WHERE sector = 'Technology'")
        logger.info("  3. Schedule monthly refresh in DataSyncManager")
        
    except Exception as e:
        logger.error(f"\n❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        classifier.close()


if __name__ == "__main__":
    main()
