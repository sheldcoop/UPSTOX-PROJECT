#!/usr/bin/env python3
"""Download Upstox instruments JSON and populate SQLite tables.

Writes to ../market_data.db using the normalized schema.
"""

import gzip
import io
import json
import sqlite3
import urllib.request
from urllib.error import URLError, HTTPError

DB_PATH = __import__("os").path.join(
    __import__("os").path.dirname(__file__), "..", "market_data.db"
)
URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"


def download_json_gz(url):
    print("Downloading", url)
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
    except (URLError, HTTPError) as e:
        raise SystemExit(f"Failed to download: {e}")
    # decompress
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
        payload = gz.read()
    return json.loads(payload.decode("utf-8"))


def populate(db_path, instruments):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    inserted_master = 0
    inserted_listing = 0

    try:
        cur.execute("BEGIN")
        for item in instruments:
            # item expected to be a dict with keys: segment, name, exchange, isin, instrument_type, instrument_key, lot_size, exchange_token, tick_size, trading_symbol, short_name
            instrument_key = item.get("instrument_key") or item.get("instrument_key")
            trading_symbol = (
                item.get("trading_symbol") or item.get("short_name") or item.get("name")
            )
            company_name = item.get("name")
            isin = item.get("isin")
            lot_size = item.get("lot_size")
            exchange = item.get("exchange")
            segment = item.get("segment")
            exchange_token = item.get("exchange_token")
            tick_size = item.get("tick_size")
            instrument_type = item.get("instrument_type")
            underlying_symbol = item.get("underlying_symbol")
            underlying_type = item.get("underlying_type")

            if not instrument_key or not trading_symbol:
                continue

            # Insert into master_stocks (symbol = trading_symbol)
            cur.execute(
                """INSERT OR IGNORE INTO master_stocks(symbol, company_name, isin, last_updated)
                   VALUES (?, ?, ?, strftime('%s','now'))""",
                (trading_symbol, company_name, isin),
            )
            if cur.rowcount:
                inserted_master += 1

            # Insert into exchange_listings
            cur.execute(
                """INSERT OR IGNORE INTO exchange_listings(instrument_key, symbol, trading_symbol, exchange, segment, exchange_token, lot_size, tick_size, instrument_type, underlying_symbol, underlying_type, last_updated)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%s','now'))""",
                (
                    instrument_key,
                    trading_symbol,
                    trading_symbol,
                    exchange,
                    segment,
                    exchange_token,
                    lot_size,
                    tick_size,
                    instrument_type,
                    underlying_symbol,
                    underlying_type,
                ),
            )
            if cur.rowcount:
                inserted_listing += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return inserted_master, inserted_listing


def main():
    instruments = download_json_gz(URL)
    if not isinstance(instruments, list):
        # some feeds wrap by keys; try to extract inner list
        # flatten dictionaries recursively
        def extract_list(obj):
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                for v in obj.values():
                    res = extract_list(v)
                    if res:
                        return res
            return None

        instruments = extract_list(instruments) or []

    print("Total instruments fetched:", len(instruments))
    inserted_master, inserted_listing = populate(DB_PATH, instruments)
    print(f"Inserted/ignored master rows: {inserted_master}")
    print(f"Inserted/ignored listing rows: {inserted_listing}")


if __name__ == "__main__":
    main()
