# NSE Indices ETL - Complete Example Workflow

This document provides a complete, step-by-step example of importing Nifty 50 constituent data into SQLite.

## Prerequisites

- SQLite 3.x installed
- Python 3.x with pandas (for standardization script)
- Bash shell
- Internet access to download NSE data

## Step 1: Setup Project Directory

```bash
# Create working directory
mkdir -p nse_etl_project
cd nse_etl_project

# Create subdirectories
mkdir -p raw_data
mkdir -p standardized_data
mkdir -p manifests
mkdir -p backups
```

## Step 2: Create Database

```bash
# Copy schema file from docs/etl/
cp /path/to/docs/etl/nse_indices_schema.sql .

# Create database
sqlite3 market_data.db < nse_indices_schema.sql

# Verify tables were created
sqlite3 market_data.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
```

Expected output:
```
companies
company_sector_map
derivatives_metadata
import_manifest
index_constituents
indices
sectors
sqlite_sequence
sqlite_stat1
```

## Step 3: Download Raw Data

### Option A: Manual Download (if NSE API requires authentication)

1. Navigate to: https://www.nseindia.com/market-data/live-equity-market
2. Select "NIFTY 50" from index dropdown
3. Click "Download" to get CSV file
4. Save as `raw_data/nifty50_20260203.csv`

### Option B: Automated Download (if API is accessible)

```bash
# Example using curl (adjust headers as needed)
curl -o raw_data/nifty50_20260203.csv \
  -H "User-Agent: Mozilla/5.0" \
  -H "Accept: text/csv" \
  "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
```

## Step 4: Inspect Raw Data

```bash
# View first few lines
head -5 raw_data/nifty50_20260203.csv

# Count rows (excluding header)
tail -n +2 raw_data/nifty50_20260203.csv | wc -l
```

Example raw CSV format:
```csv
Symbol,Company Name,Industry,Index Weight,ISIN
RELIANCE,Reliance Industries Ltd,Oil & Gas,10.25%,INE002A01018
TCS,Tata Consultancy Services Ltd,IT Services,7.89%,INE467B01029
HDFCBANK,HDFC Bank Ltd,Banking,7.45%,INE040A01034
```

## Step 5: Standardize Data

```bash
# Copy standardization script
cp /path/to/docs/etl/standardize_nse_data.py .

# Run standardization
python3 standardize_nse_data.py \
  raw_data/nifty50_20260203.csv \
  NIFTY50 \
  broad
```

Output:
```
Reading raw CSV: raw_data/nifty50_20260203.csv
Original columns: ['Symbol', 'Company Name', 'Industry', 'Index Weight', 'ISIN']
Original rows: 50

Validating data...

Standardization complete:
  Input rows: 50
  Output rows: 50
  Missing ISIN: 0 (0.00%)
  Total weight: 100.00%

Saving to: standardized_raw_data/nifty50_20260203.csv
Saving manifest to: standardized_raw_data/nifty50_20260203_manifest.json

✓ Standardization complete!
✓ Ready for import using: ./sample_import_script.sh standardized_raw_data/nifty50_20260203.csv NIFTY50
```

Generated files:
- `standardized_raw_data/nifty50_20260203.csv` - Standardized data
- `standardized_raw_data/nifty50_20260203_manifest.json` - Metadata

## Step 6: Review Standardized Data

```bash
# View standardized CSV structure
head -3 standardized_raw_data/nifty50_20260203.csv
```

Expected format:
```csv
index_code,index_name,index_type,company_name,symbol,isin,weight,market_cap,free_float_factor,effective_date,source_file_name,raw_row_json
NIFTY50,Nifty 50 Index,broad,Reliance Industries Ltd,RELIANCE,INE002A01018,10.25,,,2026-02-03,nifty50_20260203.csv,"{""Symbol"":""RELIANCE"",""Company Name"":""Reliance Industries Ltd"",...}"
NIFTY50,Nifty 50 Index,broad,Tata Consultancy Services Ltd,TCS,INE467B01029,7.89,,,2026-02-03,nifty50_20260203.csv,"{""Symbol"":""TCS"",...}"
```

## Step 7: Backup Database (Before Import)

```bash
# Create backup
sqlite3 market_data.db ".backup backups/market_data_$(date +%Y%m%d_%H%M%S).db"

# Verify backup
ls -lh backups/
```

## Step 8: Import Data

```bash
# Copy import script
cp /path/to/docs/etl/sample_import_script.sh .
chmod +x sample_import_script.sh

# Run import
./sample_import_script.sh \
  standardized_raw_data/nifty50_20260203.csv \
  NIFTY50
```

Expected output:
```
[INFO] File hash: a1b2c3d4e5f6...
[INFO] Import timestamp: 2026-02-03T14:30:00Z
[INFO] Expected rows: 50
[INFO] Creating staging table...
[INFO] Importing CSV into staging table...
[INFO] Rows staged: 50
[INFO] Validating ISINs...
[WARN] Rows with missing ISIN: 0
[INFO] Missing ISIN percentage: 0.00%
[INFO] Inserting index metadata...
[INFO] Upserting companies...
[INFO] Linking constituents to indices...
[INFO] Rows imported: 50
[INFO] Rows flagged: 0
[INFO] Creating indexes...
[INFO] Analyzing database...
[INFO] Generating manifest: ./manifests/manifest_NIFTY50_20260203_143000.json
═══════════════════════════════════════════════
Import completed successfully!
═══════════════════════════════════════════════
Index: NIFTY50
CSV File: standardized_raw_data/nifty50_20260203.csv
Rows Expected: 50
Rows Imported: 50
Rows Flagged: 0
Manifest: ./manifests/manifest_NIFTY50_20260203_143000.json
═══════════════════════════════════════════════

Running verification query...
NIFTY50|Nifty 50 Index|50|100.0

Import process complete!
```

## Step 9: Validate Import

### Query 1: Check Index Metadata
```bash
sqlite3 market_data.db <<'SQL'
SELECT index_code, index_name, index_type 
FROM indices 
WHERE index_code = 'NIFTY50';
SQL
```

Expected:
```
NIFTY50|Nifty 50 Index|broad
```

### Query 2: Check Top 10 Constituents
```bash
sqlite3 market_data.db <<'SQL'
SELECT c.symbol, c.company_name, ic.weight
FROM companies c
JOIN index_constituents ic ON ic.company_id = c.id
JOIN indices i ON i.id = ic.index_id
WHERE i.index_code = 'NIFTY50'
ORDER BY ic.weight DESC
LIMIT 10;
SQL
```

Expected:
```
RELIANCE|Reliance Industries Ltd|10.25
TCS|Tata Consultancy Services Ltd|7.89
HDFCBANK|HDFC Bank Ltd|7.45
...
```

### Query 3: Verify Total Weight
```bash
sqlite3 market_data.db <<'SQL'
SELECT 
  i.index_code,
  COUNT(ic.id) as constituent_count,
  ROUND(SUM(ic.weight), 2) as total_weight
FROM indices i
JOIN index_constituents ic ON ic.index_id = i.id
WHERE i.index_code = 'NIFTY50'
GROUP BY i.index_code;
SQL
```

Expected:
```
NIFTY50|50|100.0
```

### Query 4: Check for Missing ISINs
```bash
sqlite3 market_data.db <<'SQL'
SELECT COUNT(*) as missing_isin
FROM index_constituents ic
LEFT JOIN companies c ON c.id = ic.company_id
WHERE c.isin IS NULL OR c.isin = '';
SQL
```

Expected:
```
0
```

## Step 10: Review Import Manifest

```bash
# View manifest
cat manifests/manifest_NIFTY50_20260203_143000.json | python3 -m json.tool
```

Expected:
```json
{
  "source_url": "manual_import",
  "source_file_name": "nifty50_20260203.csv",
  "file_hash": "a1b2c3d4e5f6g7h8...",
  "download_timestamp": "2026-02-03T14:30:00Z",
  "rows_expected": 50,
  "rows_imported": 50,
  "rows_flagged": 0,
  "errors": [],
  "pdf_version": null,
  "isin_unresolved_count": 0,
  "row_count_delta_percent": 0.0
}
```

## Step 11: Advanced Queries

### Find Companies in Multiple Indices (after importing more indices)
```sql
SELECT 
  c.symbol,
  c.company_name,
  GROUP_CONCAT(i.index_code) as indices,
  COUNT(DISTINCT i.id) as index_count
FROM companies c
JOIN index_constituents ic ON ic.company_id = c.id
JOIN indices i ON i.id = ic.index_id
GROUP BY c.symbol, c.company_name
HAVING index_count > 1
ORDER BY index_count DESC;
```

### Historical Weight Changes (after importing multiple dates)
```sql
SELECT 
  c.symbol,
  ic.effective_date,
  ic.weight
FROM companies c
JOIN index_constituents ic ON ic.company_id = c.id
JOIN indices i ON i.id = ic.index_id
WHERE c.symbol = 'RELIANCE' AND i.index_code = 'NIFTY50'
ORDER BY ic.effective_date DESC;
```

### Index Composition Summary
```sql
SELECT 
  i.index_code,
  i.index_type,
  COUNT(ic.id) as constituents,
  ROUND(AVG(ic.weight), 2) as avg_weight,
  ROUND(MIN(ic.weight), 2) as min_weight,
  ROUND(MAX(ic.weight), 2) as max_weight
FROM indices i
LEFT JOIN index_constituents ic ON ic.index_id = i.id
GROUP BY i.index_code, i.index_type
ORDER BY constituents DESC;
```

## Step 12: Repeat for Other Indices

Repeat steps 3-10 for other indices:
- Bank Nifty (index_code: BANKNIFTY, type: sector)
- Nifty IT (index_code: NIFTYIT, type: sector)
- Nifty Midcap 50 (index_code: NIFTYMID50, type: broad)
- etc.

## Common Issues and Solutions

### Issue 1: Duplicate Key Error

**Error:**
```
Error: UNIQUE constraint failed: companies.isin
```

**Solution:** Company already exists. This is expected for companies in multiple indices. The `INSERT OR IGNORE` handles this automatically.

### Issue 2: Foreign Key Violation

**Error:**
```
Error: FOREIGN KEY constraint failed
```

**Solution:** Ensure indices table is populated before importing constituents:
```sql
INSERT OR IGNORE INTO indices (index_code, index_name, index_type)
VALUES ('NIFTY50', 'Nifty 50 Index', 'broad');
```

### Issue 3: High ISIN Resolution Failures

**Error:**
```
[ERROR] Missing ISIN percentage exceeds threshold (0.5%)
```

**Solution:** 
1. Review flagged rows in staging table
2. Manually lookup ISINs from NSE website
3. Update standardized CSV with correct ISINs
4. Re-run import

### Issue 4: CSV Import Fails

**Error:**
```
Error: no such column
```

**Solution:** Ensure CSV has correct header row:
```bash
head -1 standardized_data/file.csv
# Should show: index_code,index_name,index_type,...
```

## Performance Optimization

### For Large Datasets (1000+ rows)

1. **Disable synchronous mode during import:**
```sql
PRAGMA synchronous = OFF;
```

2. **Use WAL mode:**
```sql
PRAGMA journal_mode = WAL;
```

3. **Create indexes AFTER import:**
Move index creation to end of import script.

4. **Use transactions:**
All imports are already wrapped in transactions in the sample script.

## Maintenance Tasks

### Weekly: Check Import History
```sql
SELECT 
  source_file_name,
  rows_imported,
  rows_flagged,
  download_timestamp
FROM import_manifest
WHERE download_timestamp > date('now', '-7 days')
ORDER BY download_timestamp DESC;
```

### Monthly: Verify Data Integrity
```sql
-- Check for orphaned constituents
SELECT COUNT(*) FROM index_constituents ic
WHERE NOT EXISTS (SELECT 1 FROM companies c WHERE c.id = ic.company_id);

-- Check for indices without constituents
SELECT i.index_code, COUNT(ic.id) as constituents
FROM indices i
LEFT JOIN index_constituents ic ON ic.index_id = i.id
GROUP BY i.index_code
HAVING constituents = 0;
```

### Quarterly: Archive Old Data
```bash
# Backup database
sqlite3 market_data.db ".backup archive_$(date +%Y%m%d).db"

# Compress
gzip archive_$(date +%Y%m%d).db

# Move to archive directory
mv archive_$(date +%Y%m%d).db.gz /path/to/archive/
```

## Next Steps

1. Import sector indices (Auto, Bank, IT, Pharma, etc.)
2. Import thematic indices
3. Import derivatives metadata
4. Set up automated daily/weekly imports
5. Integrate with trading application

## Additional Resources

- [NSE_INDICES_ETL_CHECKLIST.md](NSE_INDICES_ETL_CHECKLIST.md) - Complete specification
- [NSE_ETL_QUICK_REFERENCE.md](NSE_ETL_QUICK_REFERENCE.md) - Quick reference guide
- [etl/README.md](etl/README.md) - Detailed ETL documentation

---

**Example Completion Time:** 15-20 minutes per index  
**Database Size:** ~1-2 MB for 5-10 indices with constituents  
**Recommended Update Frequency:** Weekly for index rebalancing
