#!/usr/bin/env python3
"""Backfill exchange_listings with instrument_type, underlying_symbol, underlying_type from CDN JSON."""

import gzip
import io
import json
import sqlite3
import urllib.request
from urllib.error import URLError, HTTPError
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "market_data.db")
URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"


def download_json_gz(url):
    print("🔄 Downloading", url)
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            data = resp.read()
    except (URLError, HTTPError) as e:
        raise SystemExit(f"❌ Failed to download: {e}")
    # decompress
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
        payload = gz.read()
    return json.loads(payload.decode("utf-8"))


def backfill(db_path, instruments):
    """Update existing exchange_listings rows with instrument_type, underlying_symbol, underlying_type."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    updated = 0
    skipped = 0

    try:
        cur.execute("BEGIN")
        for item in instruments:
            instrument_key = item.get("instrument_key")
            instrument_type = item.get("instrument_type")
            underlying_symbol = item.get("underlying_symbol")
            underlying_type = item.get("underlying_type")

            if not instrument_key:
                continue

            # Update existing row
            cur.execute(
                """UPDATE exchange_listings
                   SET instrument_type = ?, underlying_symbol = ?, underlying_type = ?
                   WHERE instrument_key = ?""",
                (instrument_type, underlying_symbol, underlying_type, instrument_key),
            )
            if cur.rowcount:
                updated += 1
            else:
                skipped += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        conn.close()

    return updated, skipped


def main():
    print("\n📊 BACKFILL exchange_listings with instrument metadata")
    print("=" * 60)
    instruments = download_json_gz(URL)

    # Flatten if needed
    if not isinstance(instruments, list):

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

    print(f"✅ Total instruments fetched: {len(instruments)}")

    updated, skipped = backfill(DB_PATH, instruments)
    print(f"\n✅ Updated rows: {updated}")
    print(f"⚠️  Skipped (no match): {skipped}")
    print(f"\n✅ Backfill complete! exchange_listings now has:")
    print("   - instrument_type")
    print("   - underlying_symbol")
    print("   - underlying_type")
    print("=" * 60)


if __name__ == "__main__":
    main()
