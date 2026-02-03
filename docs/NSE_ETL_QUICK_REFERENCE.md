# NSE Indices ETL - Quick Reference Guide

This quick reference provides links to all documentation and scripts needed for the NSE Indices ETL process.

## 📚 Documentation

### Primary Documents
- **[NSE_INDICES_ETL_CHECKLIST.md](NSE_INDICES_ETL_CHECKLIST.md)** - Complete ETL specification (510 lines)
  - Per-URL ETL checklist for 13+ NSE data sources
  - Column mapping and normalization rules
  - SQLite schema design
  - Sample queries and validation thresholds
  - Handoff checklist

- **[etl/README.md](etl/README.md)** - ETL Engineer Quick Start (224 lines)
  - Step-by-step workflow
  - Common issues and solutions
  - Validation queries
  - Best practices

## 🛠️ Scripts and Tools

### Database Setup
```bash
# Create database with schema
sqlite3 market_data.db < etl/nse_indices_schema.sql
```

**File:** [etl/nse_indices_schema.sql](etl/nse_indices_schema.sql)
- 7 tables (indices, companies, constituents, sectors, derivatives, etc.)
- 4 views (companies_with_index, index_constituents, etc.)
- 15+ indexes for performance
- Foreign key constraints
- Triggers for timestamps

### Data Standardization
```bash
# Standardize raw CSV to import format
python3 etl/standardize_nse_data.py raw_nifty50.csv NIFTY50 broad
```

**File:** [etl/standardize_nse_data.py](etl/standardize_nse_data.py)
- Normalizes weights (removes % signs)
- Converts market cap (lakhs/crores to numeric)
- Standardizes dates to ISO-8601
- Validates ISINs
- Creates audit trail (raw_row_json)
- Generates manifest JSON

### Data Import
```bash
# Import standardized CSV into SQLite
./etl/sample_import_script.sh standardized_nifty50.csv NIFTY50
```

**File:** [etl/sample_import_script.sh](etl/sample_import_script.sh)
- Creates staging tables
- Imports CSV data
- Validates ISIN resolution (0.5% threshold)
- Links constituents to indices
- Creates indexes
- Generates manifest
- Provides import summary

## 📄 Sample Files

### Manifest Template
**File:** [etl/sample_manifest.json](etl/sample_manifest.json)
```json
{
  "source_url": "...",
  "file_hash": "...",
  "rows_imported": 50,
  "rows_flagged": 0,
  "isin_unresolved_count": 0
}
```

### Standardized CSV Example
**File:** [etl/sample_standardized_constituents.csv](etl/sample_standardized_constituents.csv)
- 10 sample rows (Nifty 50 constituents)
- All required columns
- Proper formatting (weights, dates, JSON)

## 🚀 Quick Start Workflow

### 1. Initial Setup (One-time)
```bash
# Navigate to docs directory
cd docs/

# Create database
sqlite3 market_data.db < etl/nse_indices_schema.sql

# Verify tables
sqlite3 market_data.db "SELECT name FROM sqlite_master WHERE type='table';"
```

### 2. For Each Data Source

#### Download Raw Data
```bash
# Example: Nifty 50
curl -o raw_nifty50.csv "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
```

#### Standardize
```bash
python3 etl/standardize_nse_data.py raw_nifty50.csv NIFTY50 broad
# Outputs: standardized_raw_nifty50.csv
#         standardized_raw_nifty50_manifest.json
```

#### Import
```bash
./etl/sample_import_script.sh standardized_raw_nifty50.csv NIFTY50
# Creates manifest in ./manifests/
```

#### Validate
```bash
sqlite3 market_data.db <<'SQL'
-- Check constituents
SELECT c.symbol, c.company_name, ic.weight
FROM companies c
JOIN index_constituents ic ON ic.company_id = c.id
JOIN indices i ON i.id = ic.index_id
WHERE i.index_code = 'NIFTY50'
ORDER BY ic.weight DESC
LIMIT 10;
SQL
```

## 📊 Common Queries

### Get All Indices
```sql
SELECT index_code, index_name, index_type 
FROM indices 
ORDER BY index_type, index_code;
```

### Get Index Constituents
```sql
SELECT * FROM view_index_constituents 
WHERE index_code = 'NIFTY50'
ORDER BY weight DESC;
```

### Find Companies in Multiple Indices
```sql
SELECT c.symbol, c.company_name, COUNT(*) as index_count
FROM companies c
JOIN index_constituents ic ON ic.company_id = c.id
GROUP BY c.symbol
HAVING index_count > 1
ORDER BY index_count DESC;
```

### Check Import History
```sql
SELECT 
  source_file_name,
  download_timestamp,
  rows_imported,
  rows_flagged
FROM import_manifest
ORDER BY download_timestamp DESC;
```

## ⚙️ Configuration

### Database Location
Default: `market_data.db` in current directory

Override with environment variable:
```bash
export DB_FILE=/path/to/custom_db.db
./etl/sample_import_script.sh data.csv INDEX_CODE
```

### Validation Thresholds
Edit in `sample_import_script.sh`:
- Missing ISIN threshold: 0.5% (line ~90)
- Row count delta threshold: 10% (mentioned in docs)
- Parse error threshold: 0.1% (mentioned in docs)

## 🔍 Troubleshooting

### Issue: "CSV import fails"
**Solution:** Check CSV has proper header and no special characters
```bash
head -1 your_file.csv  # Verify header
```

### Issue: "ISIN not found"
**Solution:** Add company to database first
```sql
INSERT INTO companies (isin, symbol, company_name)
VALUES ('INE467B01029', 'TCS', 'Tata Consultancy Services Ltd');
```

### Issue: "Duplicate entries"
**Solution:** Clear staging table
```sql
DELETE FROM staging_constituents;
```

### Issue: "Script permission denied"
**Solution:** Make scripts executable
```bash
chmod +x etl/sample_import_script.sh
chmod +x etl/standardize_nse_data.py
```

## 📋 ETL Checklist

Before starting ETL:
- [ ] Database created with schema
- [ ] Raw data files downloaded
- [ ] Scripts have execute permissions
- [ ] Backup of existing database (if any)

For each import:
- [ ] Raw file downloaded and archived
- [ ] File hash calculated
- [ ] Data standardized
- [ ] ISIN validation passed
- [ ] Import completed successfully
- [ ] Manifest generated
- [ ] Data validated with queries

## 🗂️ File Structure

```
docs/
├── NSE_INDICES_ETL_CHECKLIST.md      # Main documentation
└── etl/
    ├── README.md                      # Quick start guide
    ├── nse_indices_schema.sql         # Database schema
    ├── sample_import_script.sh        # Import automation
    ├── standardize_nse_data.py        # Data standardization
    ├── sample_manifest.json           # Manifest template
    └── sample_standardized_constituents.csv  # CSV example
```

## 📞 Support

For detailed information:
1. Read [NSE_INDICES_ETL_CHECKLIST.md](NSE_INDICES_ETL_CHECKLIST.md)
2. Check [etl/README.md](etl/README.md) troubleshooting section
3. Review sample files in `etl/` directory

## 🔗 NSE Data Sources

- [NSE Indices Overview](https://www.nseindia.com/market-data/all-indices)
- [NSE Broad Market Indices](https://www.nseindia.com/static/products-services/indices-broad-market)
- [NSE Sector Indices](https://www.nseindia.com/market-data/live-equity-market)
- [NSE Derivatives](https://www.nseindia.com/market-data/equity-derivatives)
- [Industry Classification PDF](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/nse-indices_industry-classification-structure-2023-07.pdf)

---

**Version:** 1.0  
**Last Updated:** 2026-02-03  
**Status:** Ready for Production Use
