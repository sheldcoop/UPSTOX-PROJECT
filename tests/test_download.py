#!/usr/bin/env python3
from backend.services.market_data.downloader import StockDownloader

print("Downloading TCS 15-minute data from Upstox API...")
downloader = StockDownloader()

result = downloader.download_and_process(
    symbols=["TCS"],
    start_date="2025-01-01",
    end_date="2025-01-31",
    interval="15m",
    save_db=True,
    export_format="both",
)

print(f"\n✅ Download Complete!")
print(f"Rows downloaded: {result['rows']}")
print(f"File saved: {result['filepath']}")
print(f"Data gaps detected: {len(result['gaps'])}")

if result["rows"] > 0:
    df = result["data"]
    print(f"\nFirst 3 candles:")
    print(df[["datetime", "close", "volume"]].head(3).to_string())
    print(f"\nLast 3 candles:")
    print(df[["datetime", "close", "volume"]].tail(3).to_string())
    print(f"\nPrice range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
    print(f"Total volume: {df['volume'].sum():,}")
