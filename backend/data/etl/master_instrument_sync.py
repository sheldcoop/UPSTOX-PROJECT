#!/usr/bin/env python3
"""
🚀 Master Instrument Synchronization Pipeline
Role: ETL & Database Architect
Task: High-performance sync of Upstox CDN to 'Expert Schema' SQLite DB.
"""

import gzip
import json
import sqlite3
import logging
import requests
import time
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional

# Configuration
DB_PATH = Path("market_data.db")  # Or expert_market_data.db if separating
SCHEMA_PATH = Path('backend/database/schema/expert_schema.sql')
UPSTOX_CDN_URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/master_sync.log")
    ]
)
logger = logging.getLogger("MasterSync")

class MasterInstrumentSync:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._execution_start = time.time()
        
        # Ensure logs directory
        Path("logs").mkdir(exist_ok=True)

    def connect_db(self):
        """Connect with optimization pragmas"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging for concurrency
        self.conn.execute("PRAGMA synchronous = NORMAL;") # Balance speed/safety
        self.cursor = self.conn.cursor()

    def init_schema(self):
        """Apply the Expert Schema"""
        logger.info("🛠 Applying Expert Schema...")
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()
            self.cursor.executescript(schema_sql)
        self.conn.commit()

    def fetch_cdn_data(self) -> List[Dict]:
        """Extract: Download and decompress JSON from CDN"""
        logger.info(f"📥 Fetching Golden Record from: {UPSTOX_CDN_URL}")
        try:
            headers = {
                'User-Agent': 'Upstox-Oracle-ETL/1.0',
                'Accept-Encoding': 'gzip'
            }
            resp = requests.get(UPSTOX_CDN_URL, headers=headers, stream=True, timeout=60)
            resp.raise_for_status()
            
            # Decompress on the fly
            with gzip.GzipFile(fileobj=resp.raw) as f:
                data = json.load(f)
                
            logger.info(f"✅ Downloaded {len(data):,} instruments")
            return data
            
        except Exception as e:
            logger.error(f"❌ Critical Download Failure: {e}")
            raise

    def transform_instrument(self, raw: Dict) -> Dict:
        """Transform: Normalize raw JSON to Expert Schema format"""
        # Parse Expiry (Timestamp ms -> Date String)
        expiry_date = None
        if raw.get('expiry'):
            try:
                # Upstox sends ms timestamp
                dt = datetime.fromtimestamp(int(raw['expiry']) / 1000)
                expiry_date = dt.strftime('%Y-%m-%d')
            except:
                pass

        # Determine Security Type & Segment
        # Simple heuristic mapping
        sec_type = "STK" # Default
        inst_type = raw.get('instrument_type', 'EQ')
        segment = raw.get('segment', 'NSE_EQ')
        
        if segment in ['NSE_FO', 'MCX_FO', 'BSE_FO']:
            sec_type = "DERIVATIVE"
        elif inst_type in ['INDEX', 'IDX']:
            sec_type = "IND"
        
        return {
            'instrument_key': raw.get('instrument_key'),
            'trading_symbol': raw.get('trading_symbol'),
            'name': raw.get('name'),
            'instrument_type': inst_type,
            'security_type': sec_type,
            'segment': segment,
            'exchange': raw.get('exchange'),
            'lot_size': raw.get('lot_size', 1),
            'tick_size': raw.get('tick_size', 0.05),
            'freeze_quantity': raw.get('freeze_quantity', 0),
            'underlying_key': raw.get('underlying_key'), # FK
            'expiry': expiry_date,
            'strike_price': raw.get('strike_price') or raw.get('strike'),
            'is_active': 1
        }

    def load_bulk_upsert(self, instruments: List[Dict]):
        """Load: High-performance Batch UPSERT"""
        logger.info("🚀 Starting Batch UPSERT...")
        
        # Prepare SQL for UPSERT
        # Updates rules (Lot/Freeze) if exists, keeps static ID info
        sql = """
        INSERT INTO instrument_master (
            instrument_key, trading_symbol, name, instrument_type, 
            security_type, segment, exchange, lot_size, tick_size, 
            freeze_quantity, underlying_key, expiry, strike_price, is_active
        ) VALUES (
            :instrument_key, :trading_symbol, :name, :instrument_type, 
            :security_type, :segment, :exchange, :lot_size, :tick_size, 
            :freeze_quantity, :underlying_key, :expiry, :strike_price, :is_active
        )
        ON CONFLICT(instrument_key) DO UPDATE SET
            trading_symbol = excluded.trading_symbol,
            lot_size = excluded.lot_size,
            tick_size = excluded.tick_size,
            freeze_quantity = excluded.freeze_quantity,
            expiry = excluded.expiry,
            strike_price = excluded.strike_price,
            is_active = 1,
            last_updated = CURRENT_TIMESTAMP;
        """
        
        batch_size = 10000
        total = len(instruments)
        processed = 0
        
        try:
            # Disable FKs for bulk load (orphaned derivatives handling)
            self.conn.execute("PRAGMA foreign_keys = OFF;")
            self.conn.execute("BEGIN TRANSACTION;")
            
            batch = []
            for inst in instruments:
                transformed = self.transform_instrument(inst)
                batch.append(transformed)
                
                if len(batch) >= batch_size:
                    self.cursor.executemany(sql, batch)
                    processed += len(batch)
                    batch = []
                    print(f"   ... Processed {processed}/{total} ({round(processed/total*100)}%)", end='\r')
            
            if batch:
                self.cursor.executemany(sql, batch)
                
            self.conn.commit()
            logger.info(f"\n✅ ETL Complete. Upserted {total} records.")
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Batch Insert Failed: {e}")
            raise

    def cleanup_expired(self, current_keys: set):
        """Cleanup: active instruments in DB - current_keys = Expired"""
        logger.info("🧹 Flagging Expired Instruments...")
        
        # 1. Get all active keys from DB
        self.cursor.execute("SELECT instrument_key FROM instrument_master WHERE is_active=1")
        db_keys = set(row[0] for row in self.cursor.fetchall())
        
        # 2. Identify missing keys
        expired_keys = db_keys - current_keys
        
        if expired_keys:
            logger.info(f"   Found {len(expired_keys)} expired/missing instruments.")
            
            # Batch update to is_active=0
            # Chunking for SQLite limits
            expired_list = list(expired_keys)
            chunk_size = 900 # SQLite limit is usually 999 vars
            
            self.conn.execute("BEGIN TRANSACTION;")
            for i in range(0, len(expired_list), chunk_size):
                chunk = expired_list[i:i+chunk_size]
                placeholders = ','.join('?' * len(chunk))
                self.cursor.execute(
                    f"UPDATE instrument_master SET is_active=0 WHERE instrument_key IN ({placeholders})",
                    chunk
                )
            self.conn.commit()
            logger.info("✅ Expired instruments flagged inactive.")
        else:
            logger.info("✨ No expired instruments found.")

    def run_vacuum(self):
        """Maintenance: Rebuild DB file"""
        logger.info("🧹 VACUUMing database...")
        self.conn.execute("VACUUM;")
        logger.info("✅ Optimization Complete.")

    def run(self):
        """Execute Full Pipeline"""
        try:
            self.connect_db()
            self.init_schema()
            
            # 1. Extract
            data = self.fetch_cdn_data()
            
            # Track keys for cleanup
            current_keys = set(d.get('instrument_key') for d in data)
            
            # 2. Transform & Load
            self.load_bulk_upsert(data)
            
            # 3. Cleanup
            self.cleanup_expired(current_keys)
            
            # 4. Maintenance
            # Only vacuum on Sundays or explicitly requested (skipped for daily speed, unless requested)
            # User requirement: "VACUUMed weekly". We'll do it if it's Sunday
            if date.today().weekday() == 6: 
                self.run_vacuum()
                
            duration = time.time() - self._execution_start
            logger.info(f"🏁 Sync Finished in {duration:.2f} seconds.")
            
        except Exception as e:
            logger.error(f"🚨 Pipeline Failed: {e}")
        finally:
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    syncer = MasterInstrumentSync()
    syncer.run()
