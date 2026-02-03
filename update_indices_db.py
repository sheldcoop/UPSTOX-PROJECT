import requests
import pandas as pd
import sqlite3
import io
import time

DB_PATH = "market_data.db"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def create_metadata_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # improved schema to hold index memberships and sector
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS stock_metadata (
        symbol TEXT PRIMARY KEY,
        company_name TEXT,
        sector TEXT,
        is_nifty50 BOOLEAN DEFAULT 0,
        is_nifty500 BOOLEAN DEFAULT 0,
        is_nifty_bank BOOLEAN DEFAULT 0,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
    conn.commit()
    conn.close()
    print("✅ Metadata table ready.")


def fetch_and_process(url, tag_col):
    print(f"⬇️ Fetching {tag_col} from {url}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        # Decode content
        content = response.content.decode("utf-8")
        df = pd.read_csv(io.StringIO(content))
        return df
    except Exception as e:
        print(f"❌ Failed to fetch {tag_col}: {e}")
        return None


def update_db():
    create_metadata_table()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. NIFTY 500 (Has Sector info usually under 'Industry')
    # URL might change, using standard archive URLs
    url_500 = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    df_500 = fetch_and_process(url_500, "NIFTY 500")

    if df_500 is not None:
        # Columns often: 'Company Name', 'Industry', 'Symbol', 'Series', 'ISIN Code'
        # Clean column names
        df_500.columns = [c.strip() for c in df_500.columns]

        print(f"   Processing {len(df_500)} rows...")
        for _, row in df_500.iterrows():
            sym = row.get("Symbol")
            sector = row.get("Industry")
            name = row.get("Company Name")

            if sym:
                # Insert or Update
                cursor.execute(
                    """
                INSERT INTO stock_metadata (symbol, company_name, sector, is_nifty500)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(symbol) DO UPDATE SET
                    company_name=excluded.company_name,
                    sector=excluded.sector,
                    is_nifty500=1
                """,
                    (sym, name, sector),
                )
        print("✅ NIFTY 500 & Sectors updated.")

    # 2. NIFTY 50 (Subset, to tag specific 50)
    time.sleep(1)  # Be nice to NSE server
    url_50 = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
    df_50 = fetch_and_process(url_50, "NIFTY 50")

    if df_50 is not None:
        df_50.columns = [c.strip() for c in df_50.columns]
        count = 0
        for _, row in df_50.iterrows():
            sym = row.get("Symbol")
            if sym:
                cursor.execute(
                    "INSERT INTO stock_metadata (symbol, is_nifty50) VALUES (?, 1) ON CONFLICT(symbol) DO UPDATE SET is_nifty50=1",
                    (sym,),
                )
                count += 1
        print(f"✅ Tagged {count} NIFTY 50 stocks.")

    # 3. NIFTY BANK
    time.sleep(1)
    url_bank = "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv"
    df_bank = fetch_and_process(url_bank, "NIFTY BANK")

    if df_bank is not None:
        df_bank.columns = [c.strip() for c in df_bank.columns]
        count = 0
        for _, row in df_bank.iterrows():
            sym = row.get("Symbol")
            if sym:
                cursor.execute(
                    "INSERT INTO stock_metadata (symbol, is_nifty_bank) VALUES (?, 1) ON CONFLICT(symbol) DO UPDATE SET is_nifty_bank=1",
                    (sym,),
                )
                count += 1
        print(f"✅ Tagged {count} NIFTY BANK stocks.")

    conn.commit()

    # Verification
    print("\n--- Stats ---")
    print(
        "Stocks with Sector:",
        cursor.execute(
            "SELECT count(*) FROM stock_metadata WHERE sector IS NOT NULL"
        ).fetchone()[0],
    )
    print(
        "NIFTY 50 count:",
        cursor.execute(
            "SELECT count(*) FROM stock_metadata WHERE is_nifty50=1"
        ).fetchone()[0],
    )
    print(
        "NIFTY 500 count:",
        cursor.execute(
            "SELECT count(*) FROM stock_metadata WHERE is_nifty500=1"
        ).fetchone()[0],
    )

    conn.close()


if __name__ == "__main__":
    update_db()
