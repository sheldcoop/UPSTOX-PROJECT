#!/usr/bin/env python3
from scripts.data_downloader import StockDownloader

print("Downloading TCS data for Friday, Jan 31, 2025 (5-minute intervals)...")
downloader = StockDownloader()

result = downloader.download_and_process(
    symbols=['TCS'],
    start_date='2025-01-31',
    end_date='2025-01-31',
    interval='5m',
    save_db=True,
    export_format='both'
)

print(f"\n✅ Friday Download Complete!")
print(f"Rows downloaded: {result['rows']}")
print(f"File saved: {result['filepath']}")

if result['rows'] > 0:
    df = result['data']
    print(f"\n📊 Friday Jan 31, 2025 - TCS 5-minute data:")
    print(f"Market Open (9:15 AM): ₹{df.iloc[-1]['open']:.2f}")
    print(f"Market Close (3:30 PM): ₹{df.iloc[0]['close']:.2f}")
    print(f"Day High: ₹{df['high'].max():.2f}")
    print(f"Day Low: ₹{df['low'].min():.2f}")
    print(f"Total Volume: {df['volume'].sum():,}")
    print(f"\nTotal candles: {len(df)}")
    print(f"\nFirst 5 candles (Market Open):")
    print(df[['datetime', 'open', 'high', 'low', 'close', 'volume']].tail(5).to_string())
    print(f"\nLast 5 candles (Market Close):")
    print(df[['datetime', 'open', 'high', 'low', 'close', 'volume']].head(5).to_string())
