#!/usr/bin/env python3
"""
NSE Indices ETL Pipeline
Fetches all NSE indices data (Broad, Sectoral, Thematic) and populates database
"""

import requests
import csv
import sqlite3
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import io

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "market_data.db"

# NSE requires proper headers
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


class NSEIndicesFetcher:
    """Fetch and populate NSE indices data"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update(NSE_HEADERS)
        self.stats = {
            "indices_processed": 0,
            "constituents_inserted": 0,
            "constituents_updated": 0,
            "sectors_created": 0,
            "errors": 0
        }
    
    def fetch_csv(self, url: str, index_code: str) -> List[Dict]:
        """Download and parse CSV from NSE"""
        try:
            logger.info(f"Fetching {index_code} from NSE...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            content = response.content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            
            data = []
            for row in reader:
                # Clean column names (NSE CSVs have inconsistent naming)
                cleaned_row = {k.strip(): v.strip() for k, v in row.items() if k}
                if cleaned_row.get('Symbol') or cleaned_row.get('symbol'):
                    data.append(cleaned_row)
            
            logger.info(f"✅ Fetched {len(data)} constituents for {index_code}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error fetching {index_code}: {e}")
            self.stats["errors"] += 1
            return []
    
    def insert_constituents(self, index_code: str, data: List[Dict]) -> Tuple[int, int]:
        """Insert index constituents into database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted = 0
        updated = 0
        
        for row in data:
            # Handle different CSV column naming conventions
            symbol = row.get('Symbol') or row.get('symbol', '').strip()
            company_name = row.get('Company Name') or row.get('company_name', '').strip()
            series = row.get('Series') or row.get('series', '').strip()
            isin = row.get('ISIN Code') or row.get('isin', '').strip()
            industry = row.get('Industry') or row.get('industry', '').strip()
            
            if not symbol:
                continue
            
            try:
                # Insert/update constituent
                cursor.execute("""
                    INSERT INTO index_constituents 
                    (index_code, symbol, company_name, series, isin, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(index_code, symbol) DO UPDATE SET
                        company_name = excluded.company_name,
                        series = excluded.series,
                        isin = excluded.isin,
                        is_active = 1,
                        last_updated = excluded.last_updated
                """, (index_code, symbol, company_name, series, isin, datetime.now()))
                
                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
                
                # Extract and store sector information
                if industry:
                    self._update_sector_info(cursor, symbol, company_name, industry)
                
            except Exception as e:
                logger.error(f"Error inserting {symbol}: {e}")
                self.stats["errors"] += 1
        
        conn.commit()
        conn.close()
        
        return inserted, updated
    
    def _update_sector_info(self, cursor, symbol: str, company_name: str, industry: str):
        """Extract sector from industry and update tables"""
        # Industry format is often "Sector - Subsector" or just "Sector"
        if ' - ' in industry:
            sector_name = industry.split(' - ')[0].strip()
            sub_industry = industry.split(' - ')[1].strip() if len(industry.split(' - ')) > 1 else None
        else:
            sector_name = industry.strip()
            sub_industry = None
        
        # Insert sector if new
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO sectors (sector_name)
                VALUES (?)
            """, (sector_name,))
            
            if cursor.rowcount > 0:
                self.stats["sectors_created"] += 1
        except:
            pass
        
        # Get sector ID
        cursor.execute("SELECT id FROM sectors WHERE sector_name = ?", (sector_name,))
        result = cursor.fetchone()
        sector_id = result[0] if result else None
        
        # Update stock_sectors
        if sector_id:
            cursor.execute("""
                INSERT INTO stock_sectors (symbol, company_name, sector_id, industry, sub_industry, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    company_name = excluded.company_name,
                    sector_id = excluded.sector_id,
                    industry = excluded.industry,
                    sub_industry = excluded.sub_industry,
                    last_updated = excluded.last_updated
            """, (symbol, company_name, sector_id, industry, sub_industry, datetime.now()))
    
    def fetch_all_indices(self):
        """Fetch all indices from index_master table"""
        logger.info("=" * 70)
        logger.info("NSE INDICES ETL PIPELINE")
        logger.info("=" * 70)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all indices with CSV URLs
        cursor.execute("""
            SELECT index_code, index_name, index_category, csv_url
            FROM index_master
            WHERE csv_url IS NOT NULL
            ORDER BY index_category, index_code
        """)
        
        indices = cursor.fetchall()
        conn.close()
        
        logger.info(f"Found {len(indices)} indices to fetch\n")
        
        for index_code, index_name, category, csv_url in indices:
            logger.info(f"📊 Processing: {index_name} ({category})")
            
            # Fetch CSV data
            data = self.fetch_csv(csv_url, index_code)
            
            if data:
                # Insert constituents
                inserted, updated = self.insert_constituents(index_code, data)
                self.stats["indices_processed"] += 1
                self.stats["constituents_inserted"] += inserted
                self.stats["constituents_updated"] += updated
                
                logger.info(f"   ✓ {inserted} inserted, {updated} updated")
            
            # Be nice to NSE servers
            time.sleep(2)
            logger.info("")
        
        self._print_summary()
    
    def _print_summary(self):
        """Print execution summary"""
        logger.info("=" * 70)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Indices processed:      {self.stats['indices_processed']}")
        logger.info(f"Constituents inserted:  {self.stats['constituents_inserted']}")
        logger.info(f"Constituents updated:   {self.stats['constituents_updated']}")
        logger.info(f"Sectors created:        {self.stats['sectors_created']}")
        logger.info(f"Errors:                 {self.stats['errors']}")
        logger.info("=" * 70)
        
        # Verify data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        logger.info("\nDATABASE STATISTICS:")
        logger.info("-" * 70)
        
        cursor.execute("SELECT COUNT(*) FROM index_constituents WHERE is_active = 1")
        logger.info(f"Total active constituents: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM index_constituents WHERE is_active = 1")
        logger.info(f"Unique stocks:             {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM sectors")
        logger.info(f"Total sectors:             {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM stock_sectors")
        logger.info(f"Stocks with sector info:   {cursor.fetchone()[0]}")
        
        logger.info("\nSAMPLE QUERIES:")
        logger.info("-" * 70)
        
        # Nifty 50 count
        cursor.execute("SELECT COUNT(*) FROM index_constituents WHERE index_code = 'NIFTY50' AND is_active = 1")
        logger.info(f"Nifty 50 constituents:     {cursor.fetchone()[0]}")
        
        # Nifty 500 count
        cursor.execute("SELECT COUNT(*) FROM index_constituents WHERE index_code = 'NIFTY500' AND is_active = 1")
        logger.info(f"Nifty 500 constituents:    {cursor.fetchone()[0]}")
        
        # Top 5 sectors
        cursor.execute("""
            SELECT s.sector_name, COUNT(ss.symbol) as stock_count
            FROM sectors s
            JOIN stock_sectors ss ON s.id = ss.sector_id
            GROUP BY s.sector_name
            ORDER BY stock_count DESC
            LIMIT 5
        """)
        
        logger.info("\nTop 5 Sectors by Stock Count:")
        for sector, count in cursor.fetchall():
            logger.info(f"  • {sector}: {count} stocks")
        
        conn.close()
        logger.info("=" * 70)


def main():
    """Main execution"""
    fetcher = NSEIndicesFetcher()
    fetcher.fetch_all_indices()
    
    logger.info("\n✅ NSE Indices ETL completed successfully!")
    logger.info("Next steps:")
    logger.info("  1. Run Upstox instruments fetcher")
    logger.info("  2. Test movers service")
    logger.info("  3. Verify NiceGUI dashboard")


if __name__ == "__main__":
    main()
