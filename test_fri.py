from scripts.data_downloader import StockDownloader
d = StockDownloader()
r = d.download_and_process(['TCS'], '2025-01-31', '2025-01-31', '5m', True, 'both')
print(f"Downloaded {r['rows']} rows")
print(f"File: {r['filepath']}")
