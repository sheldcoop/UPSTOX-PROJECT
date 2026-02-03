#!/usr/bin/env python3
"""
NSE Index Data Downloader and Database Updater
Downloads NSE index constituent data and updates database with index membership and sector information
"""

import requests
import csv
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import time

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# NSE Index URLs
NSE_INDICES = {
    "NIFTY50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "NIFTYNEXT50": "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
    "NIFTY100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "NIFTY200": "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
    "NIFTY500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "NIFTYMIDCAP50": "https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv",
    "NIFTYMIDCAP100": "https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
    "NIFTYSMALLCAP50": "https://archives.nseindia.com/content/indices/ind_niftysmallcap50list.csv",
    "NIFTYSMALLCAP100": "https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
}

DB_PATH = "market_data.db"


class NSEIndexUpdater:
    """Download NSE index data and update database"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.session = requests.Session()
        # NSE requires proper headers to avoid 403
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )

    def init_database(self):
        """Create index membership and sector tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create index membership table with market cap category
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS nse_index_membership (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                company_name TEXT,
                index_name TEXT NOT NULL,
                index_category TEXT,
                index_description TEXT,
                series TEXT,
                isin TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, index_name)
            )
        """
        )

        # Create index on symbol for faster lookups
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_symbol ON nse_index_membership(symbol)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_index_name ON nse_index_membership(index_name)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_index_category ON nse_index_membership(index_category)
        """
        )

        # Create sector information table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS nse_sector_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                company_name TEXT,
                sector TEXT,
                industry TEXT,
                market_cap_category TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sector ON nse_sector_info(sector)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_cap_category ON nse_sector_info(market_cap_category)
        """
        )

        conn.commit()
        conn.close()
        logger.info("✅ Database tables created/verified")

    def download_index_data(self, index_name, url):
        """Download CSV data for an index"""
        try:
            logger.info(f"Downloading {index_name} from {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Decode content
            content = response.content.decode("utf-8")
            lines = content.split("\n")

            # Parse CSV
            reader = csv.DictReader(lines)
            data = []
            for row in reader:
                if row.get("Symbol"):  # Skip empty rows
                    data.append(row)

            logger.info(f"✅ Downloaded {len(data)} stocks for {index_name}")
            return data

        except Exception as e:
            logger.error(f"❌ Error downloading {index_name}: {str(e)}")
            return []

    def update_index_membership(self, index_name, data):
        """Update database with index membership data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        inserted = 0
        updated = 0

        for row in data:
            symbol = row.get("Symbol", "").strip()
            company_name = row.get("Company Name", "").strip()
            series = row.get("Series", "").strip()
            isin = row.get("ISIN Code", "").strip()
            industry = row.get("Industry", "").strip()

            if not symbol:
                continue

            try:
                # Insert or update index membership
                cursor.execute(
                    """
                    INSERT INTO nse_index_membership 
                    (symbol, company_name, index_name, series, isin, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(symbol, index_name) DO UPDATE SET
                        company_name = excluded.company_name,
                        series = excluded.series,
                        isin = excluded.isin,
                        updated_at = excluded.updated_at
                """,
                    (symbol, company_name, index_name, series, isin, datetime.now()),
                )

                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1

                # Update sector information if available
                if industry:
                    # Extract sector from industry (first part usually)
                    sector = (
                        industry.split("-")[0].strip() if "-" in industry else industry
                    )

                    cursor.execute(
                        """
                        INSERT INTO nse_sector_info 
                        (symbol, company_name, sector, industry, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(symbol) DO UPDATE SET
                            company_name = excluded.company_name,
                            sector = excluded.sector,
                            industry = excluded.industry,
                            updated_at = excluded.updated_at
                    """,
                        (symbol, company_name, sector, industry, datetime.now()),
                    )

            except Exception as e:
                logger.error(f"Error updating {symbol}: {str(e)}")

        conn.commit()
        conn.close()

        logger.info(f"✅ {index_name}: {inserted} inserted, {updated} updated")
        return inserted, updated

    def update_all_indices(self):
        """Download and update all indices"""
        logger.info("Starting NSE index data update...")
        self.init_database()

        total_inserted = 0
        total_updated = 0

        for index_name, index_info in NSE_INDICES.items():
            data = self.download_index_data(index_name, index_info)
            if data:
                inserted, updated = self.update_index_membership(
                    index_name, data, index_info
                )
                total_inserted += inserted
                total_updated += updated
                time.sleep(2)  # Be nice to NSE servers

        logger.info(f"")
        logger.info(f"=" * 60)
        logger.info(f"NSE Index Update Complete!")
        logger.info(f"Total inserted: {total_inserted}")
        logger.info(f"Total updated: {total_updated}")
        logger.info(f"=" * 60)

    def get_stock_indices(self, symbol):
        """Get all indices a stock belongs to"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT index_name FROM nse_index_membership
            WHERE symbol = ?
            ORDER BY index_name
        """,
            (symbol,),
        )

        indices = [row[0] for row in cursor.fetchall()]
        conn.close()
        return indices

    def get_stock_sector(self, symbol):
        """Get sector information for a stock"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT sector, industry FROM nse_sector_info
            WHERE symbol = ?
        """,
            (symbol,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {"sector": result[0], "industry": result[1]}
        return None

    def get_index_constituents(self, index_name):
        """Get all stocks in an index"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT symbol, company_name, series, isin
            FROM nse_index_membership
            WHERE index_name = ?
            ORDER BY symbol
        """,
            (index_name,),
        )

        constituents = []
        for row in cursor.fetchall():
            constituents.append(
                {
                    "symbol": row[0],
                    "company_name": row[1],
                    "series": row[2],
                    "isin": row[3],
                }
            )

        conn.close()
        return constituents

    def get_sector_stocks(self, sector):
        """Get all stocks in a sector"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT symbol, company_name, industry
            FROM nse_sector_info
            WHERE sector = ?
            ORDER BY symbol
        """,
            (sector,),
        )

        stocks = []
        for row in cursor.fetchall():
            stocks.append(
                {"symbol": row[0], "company_name": row[1], "industry": row[2]}
            )

        conn.close()
        return stocks


def main():
    """Main function"""
    updater = NSEIndexUpdater()

    logger.info("🚀 NSE Index Data Updater")
    logger.info("")

    # Update all indices
    updater.update_all_indices()

    logger.info("")
    logger.info("📊 Sample Queries:")

    # Test: Get RELIANCE info
    reliance_indices = updater.get_stock_indices("RELIANCE")
    logger.info(f"RELIANCE is in indices: {', '.join(reliance_indices)}")

    reliance_sector = updater.get_stock_sector("RELIANCE")
    if reliance_sector:
        logger.info(
            f"RELIANCE sector: {reliance_sector['sector']}, industry: {reliance_sector['industry']}"
        )

    # Test: Get NIFTY50 constituents
    nifty50 = updater.get_index_constituents("NIFTY50")
    logger.info(f"NIFTY50 has {len(nifty50)} constituents")

    logger.info("")
    logger.info("✅ Done! Database updated with NSE index and sector data")


if __name__ == "__main__":
    main()
