# NSE Indices ETL Checklist and SQLite Handoff

**Purpose:** Handoff package for an ETL engineer to ingest NSE index, sector, thematic, strategy, blended, multi‑asset, and derivatives data into a single‑user trading app using **SQLite**. Non‑destructive migrations, auditability, and ISIN‑first normalization are required.

---

## Table of Contents
1. [Per‑URL ETL Checklist](#1-perurl-etl-checklist)
2. [Column Mapping and Normalization Rules](#2-column-mapping-and-normalization-rules)
3. [PDF Classification Extraction Rules](#3-pdf-classification-extraction-rules)
4. [SQLite DDL, Compatibility Views, and Recommended Indexes](#4-sqlite-ddl-compatibility-views-and-recommended-indexes)
5. [Ingestion Order, Validation Thresholds, and Manifest Schema](#5-ingestion-order-validation-thresholds-and-manifest-schema)
6. [Sample SQLite Import Commands and Sample Queries](#6-sample-sqlite-import-commands-and-sample-queries)
7. [Handoff Checklist and Deliverables](#7-handoff-checklist-and-deliverables)

---

## 1. Per‑URL ETL Checklist

| **Source URL** | **Filename patterns to look for** | **Expected column name variants** | **One‑line extraction and mapping rule** |
|---|---|---|---|
| https://www.nseindia.com/static/products-services/indices-broad-market | `*constituents*.csv; *constituent*.csv; *index_constituents*.csv; *broad*.csv` | `Index Name; Index; Index Code; Company Name; Name; Symbol; Ticker; ISIN; Weight; Market Cap; Free Float` | Download each index constituent CSV, extract index metadata from page header if missing, set `index_type=broad`, normalize numbers/dates, resolve ISIN via master list if missing, store `source_url` and `effective_date`. |
| Sector indices hub (each sector page e.g., Auto Bank Chemicals) | `*constituents*.csv; *constituent-list*.csv; *sector-constituents*.csv` | `Sector; Index Name; Index Code; Company Name; Symbol; ISIN; Weight; Rank` | For each sector page click the sector CSV link, extract constituents, set `index_type=sector`, map sector label to PDF classification, flag mismatches. |
| https://www.nseindia.com/static/products-services/indices-thematic | `*thematic*.csv; *constituents*.csv` | `Theme; Index Name; Index Code; Company Name; Symbol; ISIN; Weight; Free Float` | Download thematic constituent CSVs, set `index_type=thematic`, normalize weights and numeric formats, record `source_file_name`. |
| https://www.nseindia.com/static/products-services/indices-strategy | `*strategy*.csv; *constituents*.csv; *rebalance*.csv` | `Strategy; Index Name; Index Code; Company Name; Symbol; ISIN; Weight; Rebalance Frequency` | Extract strategy metadata and constituents, capture rebalance frequency if present, set `index_type=strategy`, store raw row JSON for audit. |
| https://www.nseindia.com/static/products-services/indices-blended | `*blended*.csv; *constituents*.csv` | `Blended; Index Name; Index Code; Component; Company Name; Symbol; ISIN; Weight` | Ingest blended index component mapping and constituents, normalize component names and link to underlying indices where applicable. |
| https://www.nseindia.com/static/products-services/multi-asset-indices | `*multi-asset*.csv; *constituents*.csv; *components*.csv` | `Multi Asset; Index Name; Index Code; Asset Type; Ticker; ISIN; Weight` | Extract multi‑asset constituents which may include ETFs or indices, map asset type and link to indices or companies accordingly. |
| https://nsearchives.nseindia.com/web/sites/default/files/inline-files/nse-indices_industry-classification-structure-2023-07.pdf | `*.pdf` | `Sector Code; Sector Name; Industry Code; Industry Name; Sub Industry` | Run table extraction or OCR, produce CSV `classification_level,code,name,parent_code,source_page`, canonicalize codes, use for sector→industry mapping. |
| https://www.nseindia.com/static/products-services/equity-derivatives-nifty50 | `*derivative*.csv; *contract-specs*.csv; *fut*.csv; *opt*.csv` | `Market Type; Instrument Type; Symbol; Underlying; Security Descriptor; Contract Notes` | Extract FUTIDX/OPTIDX specs, normalize `instrument_type`, link `underlying` to `indices.index_code`, store `contract_notes_url`. |
| https://www.nseindia.com/static/products-services/equity-derivatives-banknifty | `*derivative*.csv; *contract-specs*.csv` | `Market Type; Instrument Type; Symbol; Underlying; Security Descriptor` | Extract contract descriptors, ensure `underlying` resolves to BankNifty index code, record `source_file_hash`. |
| https://www.nseindia.com/static/products-services/equity-derivatives-finnifty | `*derivative*.csv; *contract-specs*.csv` | `Market Type; Instrument Type; Symbol; Underlying; Security Descriptor` | Extract and normalize contract metadata, map to `indices` table. |
| https://www.nseindia.com/static/products-services/equity-derivatives-nifty-midcap-select | `*derivative*.csv; *contract-specs*.csv` | `Market Type; Instrument Type; Symbol; Underlying; Security Descriptor` | Extract contract descriptors and link `underlying` to midcap select index code. |
| https://www.nseindia.com/static/products-services/equity-derivatives-nifty-next50 | `*derivative*.csv; *contract-specs*.csv` | `Market Type; Instrument Type; Symbol; Underlying; Security Descriptor` | Extract FUTIDX/OPTIDX mapping for NIFTYNXT50 and store `instrument_type` and `market_type`. |
| https://www.nseindia.com/static/products-services/equity-derivatives-individual-securities | `*derivative*.csv; *contract-specs*.csv; *futstk*.csv; *optstk*.csv` | `Market Type; Instrument Type; Symbol; Underlying; Security Descriptor; Underlying ISIN` | For single stock derivatives, link `underlying` to `companies.isin` or `symbol`, normalize instrument types FUTSTK/OPTSTK. |

---

## 2. Column Mapping and Normalization Rules

| **Target field** | **Common source column names** | **SQLite type** |
|---|---|---|
| **index_code** | Index Code; IndexID; IDX; Index | TEXT |
| **index_name** | Index Name; Index; Index Title | TEXT |
| **index_type** | Type; Category; Index Type | TEXT |
| **effective_date** | Effective Date; As On; Date | TEXT |
| **company_name** | Company Name; Issuer; Name | TEXT |
| **symbol** | Symbol; Ticker; Trading Symbol | TEXT |
| **isin** | ISIN; ISIN Code; ISIN No | TEXT |
| **weight** | Weight; Index Weight; % Weight | REAL |
| **market_cap** | Market Cap; Mkt Cap; Market Capitalisation | REAL |
| **free_float_factor** | Free Float; Free Float Factor | REAL |
| **constituent_rank** | Rank; Sr No; Position | INTEGER |
| **sector_code** | Sector Code; SectorID; GICS Sector | TEXT |
| **industry_code** | Industry Code; IndustryID; GICS Industry | TEXT |
| **raw_row_json** | — store original row | TEXT |

**Normalization rules**
- **ISIN priority:** ISIN is authoritative. If missing, attempt symbol→ISIN lookup via exchange master list; flag unresolved rows.
- **Percent weights:** strip `%` and convert to numeric.
- **Market cap:** detect lakhs/crores suffixes and convert to plain INR numeric.
- **Dates:** convert to ISO‑8601 `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`.
- **Dedupe:** dedupe by `isin + index_code + effective_date`.
- **Audit:** store `raw_row_json` and `source_file_name` for every row.

---

## 3. PDF Classification Extraction Rules

- **Output CSV columns:** `classification_level, code, name, parent_code, source_page`.
- **Hierarchy:** top level = sector; next = industry; next = sub‑industry. Preserve `parent_code`.
- **Canonicalization:** uppercase codes and remove punctuation (e.g., `SECT-01` → `SECT01`).
- **Mapping to constituents:** exact industry name match first; if not found, fuzzy match with threshold 90%; flag fuzzy matches.
- **Versioning:** store `pdf_version` and `pdf_file_hash` in manifest.

---

## 4. SQLite DDL, Compatibility Views, and Recommended Indexes

### DDL (additive, non‑destructive)

```sql
-- Indices master table
CREATE TABLE IF NOT EXISTS indices (
  id INTEGER PRIMARY KEY,
  index_code TEXT UNIQUE,
  index_name TEXT,
  index_type TEXT,
  source_url TEXT,
  last_updated TEXT
);

-- Companies master table
CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY,
  isin TEXT UNIQUE,
  symbol TEXT,
  company_name TEXT,
  listed_exchange TEXT,
  metadata_json TEXT
);

-- Index constituents mapping
CREATE TABLE IF NOT EXISTS index_constituents (
  id INTEGER PRIMARY KEY,
  index_id INTEGER,
  company_id INTEGER,
  weight REAL,
  effective_date TEXT,
  source_csv_url TEXT,
  raw_row_json TEXT,
  FOREIGN KEY(index_id) REFERENCES indices(id),
  FOREIGN KEY(company_id) REFERENCES companies(id)
);

-- Sector/Industry classification
CREATE TABLE IF NOT EXISTS sectors (
  code TEXT PRIMARY KEY,
  name TEXT,
  parent_code TEXT,
  classification_level TEXT,
  source_page INTEGER
);

-- Company to sector mapping
CREATE TABLE IF NOT EXISTS company_sector_map (
  id INTEGER PRIMARY KEY,
  company_id INTEGER,
  sector_code TEXT,
  industry_code TEXT,
  assigned_date TEXT,
  FOREIGN KEY(company_id) REFERENCES companies(id),
  FOREIGN KEY(sector_code) REFERENCES sectors(code)
);

-- Derivatives metadata
CREATE TABLE IF NOT EXISTS derivatives_metadata (
  id INTEGER PRIMARY KEY,
  symbol TEXT,
  market_type TEXT,
  instrument_type TEXT,
  underlying TEXT,
  underlying_isin TEXT,
  security_descriptor TEXT,
  source_url TEXT,
  last_scraped TEXT
);

-- Import manifest for tracking ETL runs
CREATE TABLE IF NOT EXISTS import_manifest (
  id INTEGER PRIMARY KEY,
  source_url TEXT,
  source_file_name TEXT,
  file_hash TEXT,
  download_timestamp TEXT,
  rows_expected INTEGER,
  rows_imported INTEGER,
  rows_flagged INTEGER,
  errors_json TEXT,
  pdf_version TEXT
);
```

### Compatibility Views

```sql
-- View: Companies with their index memberships
CREATE VIEW IF NOT EXISTS view_companies_with_index AS
SELECT c.*, i.index_code, i.index_name, ic.weight, ic.effective_date
FROM companies c
JOIN index_constituents ic ON ic.company_id = c.id
JOIN indices i ON i.id = ic.index_id;

-- View: Index constituents with full details
CREATE VIEW IF NOT EXISTS view_index_constituents AS
SELECT i.index_code, i.index_name, c.isin, c.symbol, c.company_name, ic.weight, ic.effective_date
FROM index_constituents ic
JOIN indices i ON i.id = ic.index_id
JOIN companies c ON c.id = ic.company_id;
```

### Recommended Indexes (create after import)

```sql
CREATE INDEX IF NOT EXISTS idx_companies_isin ON companies(isin);
CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol);
CREATE INDEX IF NOT EXISTS idx_indices_code ON indices(index_code);
CREATE INDEX IF NOT EXISTS idx_const_idx_comp ON index_constituents(index_id, company_id);
CREATE INDEX IF NOT EXISTS idx_const_effective_date ON index_constituents(effective_date);
CREATE INDEX IF NOT EXISTS idx_derivatives_underlying ON derivatives_metadata(underlying);
```

---

## 5. Ingestion Order, Validation Thresholds, and Manifest Schema

### Ingestion Order
1. Archive raw files to external storage and record path.
2. Import classification CSV from PDF into `sectors`.
3. Import `indices` metadata.
4. Import constituent CSVs into a staging table.
5. Resolve ISINs and dedupe.
6. Insert into `index_constituents`.
7. Import `derivatives_metadata`.
8. Run integrity checks and create compatibility views.

### Validation Thresholds
- Fail run if unresolved ISINs > **0.5%** of rows.
- Flag if row count delta > **10%** vs previous run for same index.
- Fail run if parsing errors > **0.1%** of rows.

### Manifest JSON Schema Example

```json
{
  "source_url": "string",
  "source_file_name": "string",
  "file_hash": "string",
  "download_timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "rows_expected": 0,
  "rows_imported": 0,
  "rows_flagged": 0,
  "errors": [],
  "pdf_version": "string",
  "isin_unresolved_count": 0,
  "row_count_delta_percent": 0.0
}
```

---

## 6. Sample SQLite Import Commands and Sample Queries

### Sample Import Commands (CLI using `sqlite3`)

#### Step 1: Create tables (run the DDL above)

```bash
sqlite3 market_data.db < nse_indices_schema.sql
```

#### Step 2: Import a standardized CSV into staging table

```bash
# Create staging table
sqlite3 market_data.db <<'SQL'
CREATE TABLE IF NOT EXISTS staging_constituents (
  index_code TEXT,
  index_name TEXT,
  index_type TEXT,
  company_name TEXT,
  symbol TEXT,
  isin TEXT,
  weight REAL,
  market_cap REAL,
  free_float_factor REAL,
  effective_date TEXT,
  source_file_name TEXT,
  raw_row_json TEXT
);
SQL

# Import CSV
sqlite3 market_data.db <<'SQL'
.mode csv
.separator ","
.import /path/to/standardized_constituents.csv staging_constituents
SQL
```

#### Step 3: Resolve ISINs and insert into production tables

```sql
BEGIN TRANSACTION;

-- Insert indices if not exists
INSERT OR IGNORE INTO indices (index_code, index_name, index_type, source_url, last_updated)
VALUES ('NIFTY50', 'Nifty 50 Index', 'broad', 'https://www.nseindia.com/static/products-services/indices-broad-market', '2025-01-01');

-- Upsert companies by ISIN
INSERT OR IGNORE INTO companies (isin, symbol, company_name)
SELECT isin, symbol, company_name FROM staging_constituents WHERE isin IS NOT NULL;

-- Link constituents
INSERT INTO index_constituents (index_id, company_id, weight, effective_date, source_csv_url, raw_row_json)
SELECT i.id, c.id, s.weight, s.effective_date, s.source_file_name, s.raw_row_json
FROM staging_constituents s
JOIN indices i ON i.index_code = s.index_code
JOIN companies c ON c.isin = s.isin;

COMMIT;
```

### Sample Queries

#### Query 1: Which companies are in Nifty 50?

```sql
SELECT c.isin, c.symbol, c.company_name
FROM companies c
JOIN index_constituents ic ON ic.company_id = c.id
JOIN indices i ON i.id = ic.index_id
WHERE i.index_code = 'NIFTY50';
```

#### Query 2: Constituents of Auto sector index (by index_code)

```sql
SELECT c.isin, c.symbol, c.company_name, ic.weight
FROM companies c
JOIN index_constituents ic ON ic.company_id = c.id
JOIN indices i ON i.id = ic.index_id
WHERE i.index_type = 'sector' AND i.index_name LIKE '%Auto%';
```

#### Query 3: Which derivatives exist for Nifty Next 50?

```sql
SELECT d.symbol, d.instrument_type, d.market_type, d.security_descriptor
FROM derivatives_metadata d
WHERE d.underlying = 'NIFTYNXT50' 
   OR d.underlying_isin = (SELECT isin FROM indices WHERE index_code='NIFTYNXT50');
```

#### Query 4: Get all index constituents with weights

```sql
SELECT * FROM view_index_constituents
ORDER BY index_code, weight DESC;
```

#### Query 5: Companies with multiple index memberships

```sql
SELECT c.symbol, c.company_name, COUNT(DISTINCT i.index_code) as index_count
FROM companies c
JOIN index_constituents ic ON ic.company_id = c.id
JOIN indices i ON i.id = ic.index_id
GROUP BY c.symbol, c.company_name
HAVING index_count > 1
ORDER BY index_count DESC;
```

---

## 7. Handoff Checklist and Deliverables

### Pre-ETL Setup
- [ ] Raw files archived with file hashes and `raw_file_path` recorded
- [ ] Standardized CSVs produced for each source with header matching target fields
- [ ] Classification CSV from PDF included
- [ ] Derivatives metadata CSV included
- [ ] Manifest JSON for each source run included

### ETL Implementation
- [ ] Staging SQLite import script or commands documented in README
- [ ] ISIN resolution logic implemented with fallback to symbol lookup
- [ ] Deduplication logic implemented (ISIN + index_code + effective_date)
- [ ] Validation thresholds configured (0.5% ISIN errors, 10% row delta, 0.1% parse errors)
- [ ] Error handling and logging implemented

### Post-ETL Validation
- [ ] List of flagged rows requiring manual review included
- [ ] Sample queries validated on staging DB:
  - [ ] Constituents of Nifty 50
  - [ ] Constituents of Auto sector index
  - [ ] Derivatives for Nifty Next 50
- [ ] Indexes created and `ANALYZE` run
- [ ] Compatibility views verified

### Documentation
- [ ] README quick instructions for the ETL engineer provided
- [ ] Column mapping reference included
- [ ] Normalization rules documented
- [ ] Sample manifest JSON provided
- [ ] Troubleshooting guide for common issues

---

## Quick Instructions for ETL Engineer

### Step-by-Step Workflow

1. **Fetch** each source URL and archive the raw file (CSV/HTML/PDF). Record `file_hash` and `download_timestamp`.

2. **Extract** classification CSV from the PDF and load into `sectors`.
   ```bash
   # Use tabula-py or pdfplumber for PDF extraction
   python extract_classification.py nse-indices_industry-classification-structure-2023-07.pdf
   ```

3. **Standardize** each constituent CSV into the agreed schema (ISO dates, numeric normalization, `raw_row_json`).
   ```python
   # Example standardization script
   import pandas as pd
   df = pd.read_csv('raw_nifty50_constituents.csv')
   df['weight'] = df['weight'].str.replace('%', '').astype(float)
   df['effective_date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
   df['raw_row_json'] = df.apply(lambda x: x.to_json(), axis=1)
   df.to_csv('standardized_constituents.csv', index=False)
   ```

4. **Stage** standardized CSVs into a staging table. Run ISIN resolution against the exchange master list.

5. **Validate** against thresholds. If thresholds fail, stop and produce manifest with errors.

6. **Load** into production tables inside a transaction and create compatibility views.

7. **Index** the DB and run `ANALYZE`. Keep raw files off the DB and maintain manifest JSON for each run.

### Best Practices

- **WAL Mode**: Use WAL mode during ETL for better concurrency.
  ```sql
  PRAGMA journal_mode=WAL;
  ```

- **Single Writer**: Ensure only one ETL process writes at a time.

- **Backup Before Import**: Always backup the database before major imports.
  ```bash
  sqlite3 market_data.db ".backup market_data_backup_$(date +%Y%m%d).db"
  ```

- **Keep Raw Files External**: Don't store large CSVs or PDFs in the SQLite database to avoid bloat.

- **Audit Trail**: Always maintain `raw_row_json` for auditability and reprocessing.

- **Flag Ambiguous Mappings**: Symbol→ISIN mappings that are ambiguous should be flagged for manual review.

---

## Troubleshooting Guide

### Issue: High ISIN Resolution Failures

**Symptoms:** More than 0.5% of rows have unresolved ISINs.

**Solutions:**
- Check if the exchange master list is up-to-date
- Verify symbol naming conventions (some may include exchange suffix like `.NS`)
- Consider fuzzy matching for symbols with minor variations
- Flag unresolved rows for manual ISIN lookup

### Issue: Row Count Delta Exceeds 10%

**Symptoms:** Constituent count differs significantly from previous run.

**Solutions:**
- Verify the effective date is current
- Check if index underwent rebalancing
- Confirm source CSV is complete (not partial download)
- Review NSE announcements for index methodology changes

### Issue: Duplicate Entries

**Symptoms:** Same ISIN appears multiple times for same index and effective date.

**Solutions:**
- Review deduplication logic (should be ISIN + index_code + effective_date)
- Check if multiple source files have overlapping data
- Verify staging table is cleared before each import
- Use `INSERT OR IGNORE` or `INSERT OR REPLACE` appropriately

### Issue: Foreign Key Violations

**Symptoms:** Cannot insert into index_constituents due to missing references.

**Solutions:**
- Ensure indices are inserted before constituents
- Ensure companies are inserted before linking to constituents
- Use transactions to maintain referential integrity
- Verify staging data has valid index_code values

---

## Additional Resources

### Related Files
- `/docs/etl/sample_import_script.sh` - Ready-to-run staging import script
- `/docs/etl/sample_manifest.json` - Example manifest structure
- `/docs/etl/sample_standardized_constituents.csv` - Example CSV format
- `/docs/etl/README.md` - Detailed ETL engineer quickstart

### NSE Data Sources
- [NSE Indices Overview](https://www.nseindia.com/market-data/all-indices)
- [NSE Derivatives](https://www.nseindia.com/market-data/equity-derivatives)
- [NSE Industry Classification PDF](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/nse-indices_industry-classification-structure-2023-07.pdf)

### Tools Recommended
- **CSV Processing:** Python pandas, csvkit
- **PDF Extraction:** tabula-py, pdfplumber, camelot-py
- **SQLite CLI:** sqlite3 command-line tool
- **Data Validation:** Great Expectations, pandas-profiling

---

## Final Notes

- Keep raw files outside the SQLite DB to avoid bloat.
- Use WAL mode during ETL and single‑writer pattern.
- Keep `raw_row_json` for auditability and reprocessing.
- Flag ambiguous symbol→ISIN mappings for manual review.
- Always test imports on a staging database first.
- Document any deviations from this specification in the manifest `errors_json` field.

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-03  
**Contact:** ETL Engineering Team
