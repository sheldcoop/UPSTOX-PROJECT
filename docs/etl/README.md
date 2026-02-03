# NSE Indices ETL Quick Start Guide

This directory contains ready-to-use scripts and templates for importing NSE indices data into SQLite.

## Contents

- **sample_import_script.sh** - Complete bash script for staging and importing NSE constituent data
- **sample_manifest.json** - Template for ETL run manifest tracking
- **sample_standardized_constituents.csv** - Example of properly formatted constituent data
- **nse_indices_schema.sql** - Complete DDL for creating all required tables

## Quick Start

### 1. Set Up Database

```bash
# Create database and tables
sqlite3 market_data.db < nse_indices_schema.sql
```

### 2. Download and Standardize Data

```bash
# Edit the script to point to your raw CSV files
./sample_import_script.sh
```

### 3. Verify Import

```bash
sqlite3 market_data.db <<'SQL'
-- Check imported indices
SELECT index_code, index_name, index_type FROM indices;

-- Check constituent counts
SELECT i.index_code, COUNT(*) as constituents
FROM indices i
JOIN index_constituents ic ON ic.index_id = i.id
GROUP BY i.index_code;
SQL
```

## File Descriptions

### sample_import_script.sh

A complete bash script that:
- Creates staging tables
- Imports standardized CSV data
- Resolves ISINs
- Links constituents to indices
- Creates indexes
- Generates a manifest JSON

**Usage:**
```bash
chmod +x sample_import_script.sh
./sample_import_script.sh /path/to/standardized_constituents.csv NIFTY50
```

### sample_manifest.json

Template for tracking each ETL run. Fields include:
- `source_url` - Original data source URL
- `file_hash` - SHA256 hash of raw file
- `download_timestamp` - When file was downloaded
- `rows_imported` - Count of successfully imported rows
- `rows_flagged` - Count of rows requiring manual review
- `errors` - Array of error messages

### sample_standardized_constituents.csv

Example showing the required CSV format after standardization:
- All weights converted to numeric (no % signs)
- Dates in ISO format (YYYY-MM-DD)
- ISINs validated
- Raw JSON preserved for audit

### nse_indices_schema.sql

Complete DDL including:
- All table definitions
- Foreign key constraints
- Recommended indexes
- Compatibility views

## Workflow Steps

### Step 1: Fetch Raw Data

```bash
# Example: Download Nifty 50 constituents
curl -o nifty50_raw.csv "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
```

### Step 2: Standardize

```python
# Example Python script for standardization
import pandas as pd
import json

df = pd.read_csv('nifty50_raw.csv')

# Normalize weights
if 'Weight' in df.columns:
    df['weight'] = df['Weight'].str.replace('%', '').astype(float)

# Normalize dates
if 'Date' in df.columns:
    df['effective_date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

# Add metadata
df['index_code'] = 'NIFTY50'
df['index_type'] = 'broad'
df['source_file_name'] = 'nifty50_raw.csv'

# Store raw row as JSON
df['raw_row_json'] = df.apply(lambda x: x.to_json(), axis=1)

# Save standardized CSV
df.to_csv('standardized_constituents.csv', index=False)
```

### Step 3: Import

```bash
./sample_import_script.sh standardized_constituents.csv NIFTY50
```

### Step 4: Validate

```bash
# Check for errors
sqlite3 market_data.db <<'SQL'
SELECT COUNT(*) as total_rows FROM index_constituents;
SELECT COUNT(*) as missing_isin FROM index_constituents 
WHERE company_id IS NULL;
SQL
```

## Common Issues

### Issue: CSV Import Fails

**Solution:** Ensure CSV has proper header row and no special characters in column names.

```bash
# Fix CSV header
sed -i '1s/[^a-zA-Z0-9,_]//g' your_file.csv
```

### Issue: ISIN Not Found

**Solution:** Check if company exists in `companies` table. If not, insert it first.

```sql
INSERT INTO companies (isin, symbol, company_name)
VALUES ('INE467B01029', 'TCS', 'Tata Consultancy Services Ltd');
```

### Issue: Duplicate Entries

**Solution:** Clear staging table before each import.

```sql
DELETE FROM staging_constituents;
```

## Best Practices

1. **Always backup** before importing:
   ```bash
   sqlite3 market_data.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"
   ```

2. **Use transactions** for large imports to ensure atomicity

3. **Validate data** before moving from staging to production tables

4. **Keep manifests** for each import run for audit trail

5. **Archive raw files** separately from the database

## Validation Queries

### Check Import Completeness

```sql
-- Compare staging vs production row counts
SELECT 'Staging' as source, COUNT(*) as rows FROM staging_constituents
UNION ALL
SELECT 'Production' as source, COUNT(*) as rows FROM index_constituents;
```

### Check for Missing ISINs

```sql
SELECT s.symbol, s.company_name, s.isin
FROM staging_constituents s
LEFT JOIN companies c ON c.isin = s.isin
WHERE c.id IS NULL;
```

### Check Duplicate ISINs per Index

```sql
SELECT ic.company_id, i.index_code, COUNT(*) as occurrences
FROM index_constituents ic
JOIN indices i ON i.id = ic.index_id
GROUP BY ic.company_id, i.index_code
HAVING occurrences > 1;
```

## Support

For issues or questions:
1. Review the main ETL checklist: `../NSE_INDICES_ETL_CHECKLIST.md`
2. Check the troubleshooting section
3. Consult NSE official documentation

## Version History

- **v1.0** (2026-02-03) - Initial release with SQLite support
