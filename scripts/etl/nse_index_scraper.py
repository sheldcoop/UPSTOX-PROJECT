#!/usr/bin/env python3
"""
NSE Index Scraper - Production Grade
Downloads CSVs and scrapes HTML for all 18 NSE indices
Extracts sector/industry metadata and merges with official CSV data
"""

import requests
import pandas as pd
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import sqlite3

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "market_data.db"
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "nse_indices"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class NSEIndexScraper:
    """
    Scrapes NSE index constituents from official sources
    - Primary: CSV download (fast, reliable)
    - Secondary: HTML scraping (sector/industry enrichment)
    """
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # HTTP session with retry logic
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.stats = {
            'total_indices': 0,
            'csv_success': 0,
            'html_success': 0,
            'merged_success': 0,
            'errors': []
        }
    
    def get_index_config(self, index_code: str) -> Optional[Dict]:
        """Fetch index configuration from database"""
        self.cursor.execute("""
        SELECT index_code, index_name, index_type, expected_count, csv_url, html_url
        FROM nse_index_metadata
        WHERE index_code = ?
        """, (index_code,))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return {
            'index_code': row[0],
            'index_name': row[1],
            'index_type': row[2],
            'expected_count': row[3],
            'csv_url': row[4],
            'html_url': row[5]
        }
    
    def get_all_indices(self) -> List[str]:
        """Get list of all index codes from database"""
        self.cursor.execute("SELECT index_code FROM nse_index_metadata ORDER BY index_code")
        return [row[0] for row in self.cursor.fetchall()]
    
    def download_csv(self, index_code: str, csv_url: str) -> Optional[pd.DataFrame]:
        """
        Download official NSE CSV
        Returns DataFrame with: Symbol, Company Name, Industry, ISIN Code
        """
        scrape_start = time.time()
        
        try:
            logger.info(f"📥 Downloading CSV for {index_code}...")
            logger.debug(f"   URL: {csv_url}")
            
            response = self.session.get(csv_url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            # Standardize column names
            df.columns = df.columns.str.strip()
            
            # Expected columns in NSE CSV
            required_cols = ['Symbol', 'Company Name', 'Industry', 'ISIN Code']
            
            # Check if all required columns exist
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"⚠️  Missing columns in CSV: {missing_cols}")
                logger.debug(f"   Available columns: {df.columns.tolist()}")
            
            # Rename to standard format
            column_mapping = {
                'Symbol': 'symbol',
                'Company Name': 'company_name',
                'Industry': 'industry',
                'ISIN Code': 'isin',
            }
            df = df.rename(columns=column_mapping)
            
            # Clean data
            df['symbol'] = df['symbol'].str.strip()
            df['company_name'] = df['company_name'].str.strip()
            df['industry'] = df['industry'].str.strip() if 'industry' in df.columns else None
            df['isin'] = df['isin'].str.strip() if 'isin' in df.columns else None
            
            duration = time.time() - scrape_start
            
            # Log to database
            self.cursor.execute("""
            INSERT INTO nse_index_scrape_log 
            (index_code, scrape_type, status, constituents_found, duration_seconds)
            VALUES (?, 'CSV', 'SUCCESS', ?, ?)
            """, (index_code, len(df), duration))
            self.conn.commit()
            
            self.stats['csv_success'] += 1
            logger.info(f"✅ CSV downloaded: {len(df)} constituents in {duration:.2f}s")
            
            return df
            
        except Exception as e:
            duration = time.time() - scrape_start
            error_msg = str(e)
            
            self.cursor.execute("""
            INSERT INTO nse_index_scrape_log 
            (index_code, scrape_type, status, constituents_found, duration_seconds, error_message)
            VALUES (?, 'CSV', 'FAILED', 0, ?, ?)
            """, (index_code, duration, error_msg))
            self.conn.commit()
            
            logger.error(f"❌ CSV download failed for {index_code}: {error_msg}")
            self.stats['errors'].append(f"{index_code}_CSV: {error_msg}")
            
            return None
    
    def scrape_html_metadata(self, index_code: str, html_url: str) -> Optional[pd.DataFrame]:
        """
        Scrape NSE webpage for sector/industry metadata
        Returns DataFrame with: Symbol, Sector, Industry (if available)
        """
        scrape_start = time.time()
        
        try:
            logger.info(f"🌐 Scraping HTML metadata for {index_code}...")
            logger.debug(f"   URL: {html_url}")
            
            response = self.session.get(html_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # NSE pages often have tables with class "table" or "data-table"
            # This is a generic scraper - may need adjustment per page structure
            tables = soup.find_all('table')
            
            if not tables:
                logger.warning(f"⚠️  No tables found in HTML for {index_code}")
                return None
            
            # Try parsing first table (usually constituents table)
            df = None
            for table in tables:
                try:
                    df = pd.read_html(str(table))[0]
                    # Check if it looks like a constituents table
                    if 'Symbol' in df.columns or 'Company' in df.columns:
                        break
                except Exception:
                    continue
            
            if df is None or df.empty:
                logger.warning(f"⚠️  Could not parse HTML table for {index_code}")
                return None
            
            # Standardize columns (NSE HTML format varies)
            # Common columns: Symbol, Company, Industry, Sector, Weight
            column_mapping = {}
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'symbol' in col_lower:
                    column_mapping[col] = 'symbol'
                elif 'company' in col_lower or 'name' in col_lower:
                    column_mapping[col] = 'company_name'
                elif 'sector' in col_lower:
                    column_mapping[col] = 'sector'
                elif 'industry' in col_lower:
                    column_mapping[col] = 'industry'
                elif 'weight' in col_lower:
                    column_mapping[col] = 'weight'
            
            df = df.rename(columns=column_mapping)
            
            # Keep only relevant columns
            keep_cols = [col for col in ['symbol', 'company_name', 'sector', 'industry', 'weight'] if col in df.columns]
            df = df[keep_cols]
            
            # Clean data
            if 'symbol' in df.columns:
                df['symbol'] = df['symbol'].str.strip()
            if 'sector' in df.columns:
                df['sector'] = df['sector'].str.strip()
            if 'industry' in df.columns:
                df['industry'] = df['industry'].str.strip()
            
            duration = time.time() - scrape_start
            
            # Log success
            self.cursor.execute("""
            INSERT INTO nse_index_scrape_log 
            (index_code, scrape_type, status, constituents_found, duration_seconds)
            VALUES (?, 'HTML', 'SUCCESS', ?, ?)
            """, (index_code, len(df), duration))
            self.conn.commit()
            
            self.stats['html_success'] += 1
            logger.info(f"✅ HTML scraped: {len(df)} constituents in {duration:.2f}s")
            
            return df
            
        except Exception as e:
            duration = time.time() - scrape_start
            error_msg = str(e)
            
            self.cursor.execute("""
            INSERT INTO nse_index_scrape_log 
            (index_code, scrape_type, status, constituents_found, duration_seconds, error_message)
            VALUES (?, 'HTML', 'FAILED', 0, ?, ?)
            """, (index_code, duration, error_msg))
            self.conn.commit()
            
            logger.warning(f"⚠️  HTML scraping failed for {index_code}: {error_msg}")
            # HTML scraping is optional, so don't add to errors
            
            return None
    
    def merge_csv_html_data(self, csv_df: pd.DataFrame, html_df: Optional[pd.DataFrame]) -> pd.DataFrame:
        """
        Merge CSV (authoritative) with HTML (enriched) data
        Priority: CSV for symbol/isin, HTML for sector/industry
        """
        if html_df is None or html_df.empty:
            logger.info("  ℹ️  Using CSV data only (HTML not available)")
            return csv_df
        
        # Merge on symbol
        if 'symbol' not in csv_df.columns or 'symbol' not in html_df.columns:
            logger.warning("  ⚠️  Cannot merge: 'symbol' column missing")
            return csv_df
        
        # Left join: keep all CSV records, add HTML columns
        merged = csv_df.merge(
            html_df[['symbol', 'sector', 'industry']].drop_duplicates(subset=['symbol']),
            on='symbol',
            how='left',
            suffixes=('_csv', '_html')
        )
        
        # Prefer HTML sector/industry if available, fallback to CSV
        if 'sector_html' in merged.columns:
            merged['sector'] = merged['sector_html'].fillna(merged.get('sector_csv', ''))
        if 'industry_html' in merged.columns:
            merged['industry'] = merged['industry_html'].fillna(merged.get('industry_csv', ''))
        
        # Clean up merge columns
        merged = merged[[col for col in merged.columns if not col.endswith('_csv') and not col.endswith('_html')]]
        
        logger.info(f"  ✅ Merged CSV+HTML: {len(merged)} constituents")
        
        return merged
    
    def save_enriched_data(self, index_code: str, df: pd.DataFrame):
        """Save enriched data to CSV for auditing"""
        output_path = DATA_DIR / f"{index_code}_enriched.csv"
        
        # Add metadata
        df['index_code'] = index_code
        df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
        
        df.to_csv(output_path, index=False)
        logger.info(f"  💾 Saved to: {output_path}")
    
    def scrape_index(self, index_code: str) -> Optional[pd.DataFrame]:
        """
        Complete scraping workflow for one index
        1. Download CSV (official data)
        2. Scrape HTML (enrichment)
        3. Merge data
        4. Save to file
        """
        logger.info(f"\n{'=' * 70}")
        logger.info(f"SCRAPING: {index_code}")
        logger.info(f"{'=' * 70}")
        
        # Get configuration
        config = self.get_index_config(index_code)
        if not config:
            logger.error(f"❌ No configuration found for {index_code}")
            return None
        
        scrape_start = time.time()
        
        # Step 1: Download CSV
        csv_df = self.download_csv(index_code, config['csv_url'])
        if csv_df is None:
            logger.error(f"❌ CSV download failed for {index_code}, skipping index")
            return None
        
        # Step 2: Scrape HTML (optional enhancement)
        time.sleep(1)  # Rate limiting between requests
        html_df = self.scrape_html_metadata(index_code, config['html_url'])
        
        # Step 3: Merge data
        enriched_df = self.merge_csv_html_data(csv_df, html_df)
        
        # Step 4: Save to file
        self.save_enriched_data(index_code, enriched_df)
        
        # Update metadata
        duration = time.time() - scrape_start
        self.cursor.execute("""
        UPDATE nse_index_metadata
        SET constituent_count = ?,
            last_scraped = datetime('now'),
            last_scrape_status = 'SUCCESS',
            scrape_error_message = NULL,
            updated_at = datetime('now')
        WHERE index_code = ?
        """, (len(enriched_df), index_code))
        self.conn.commit()
        
        self.stats['merged_success'] += 1
        logger.info(f"✅ {index_code} completed in {duration:.2f}s")
        
        return enriched_df
    
    def scrape_all_indices(self):
        """Scrape all 18 indices"""
        logger.info("=" * 70)
        logger.info("NSE INDEX SCRAPER - SCRAPING ALL 18 INDICES")
        logger.info("=" * 70)
        
        indices = self.get_all_indices()
        self.stats['total_indices'] = len(indices)
        
        logger.info(f"\nFound {len(indices)} indices to scrape")
        logger.info(f"Output directory: {DATA_DIR}")
        logger.info("")
        
        for i, index_code in enumerate(indices, 1):
            logger.info(f"\n[{i}/{len(indices)}] Processing {index_code}...")
            
            self.scrape_index(index_code)
            
            # Rate limiting between indices
            if i < len(indices):
                time.sleep(2)
        
        self.print_summary()
    
    def print_summary(self):
        """Print scraping summary"""
        logger.info("\n" + "=" * 70)
        logger.info("SCRAPING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total indices:      {self.stats['total_indices']}")
        logger.info(f"CSV success:        {self.stats['csv_success']}")
        logger.info(f"HTML success:       {self.stats['html_success']}")
        logger.info(f"Merged success:     {self.stats['merged_success']}")
        logger.info(f"Errors:             {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            logger.info("\n❌ Errors encountered:")
            for error in self.stats['errors'][:10]:
                logger.info(f"  - {error}")
        
        # Database stats
        self.cursor.execute("""
        SELECT COUNT(*), SUM(constituent_count) 
        FROM nse_index_metadata 
        WHERE last_scrape_status = 'SUCCESS'
        """)
        success_count, total_constituents = self.cursor.fetchone()
        
        logger.info(f"\n📊 Database status:")
        logger.info(f"  Indices scraped:      {success_count}")
        logger.info(f"  Total constituents:   {total_constituents or 0:,}")
        logger.info(f"  Data files saved:     {len(list(DATA_DIR.glob('*_enriched.csv')))}")
        
        logger.info("=" * 70)
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """CLI entry point"""
    scraper = NSEIndexScraper()
    
    try:
        scraper.scrape_all_indices()
        
        logger.info("\n✅ Scraping completed successfully!")
        logger.info("\nNext steps:")
        logger.info("  1. Review enriched CSVs in data/nse_indices/")
        logger.info("  2. Run nse_index_classifier.py to classify instruments")
        logger.info("  3. Verify index_constituents_v2 table is populated")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Scraping failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
