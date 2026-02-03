#!/bin/bash
#
# NSE Indices ETL Import Script
# Purpose: Import standardized NSE constituent data into SQLite database
# Usage: ./sample_import_script.sh <csv_file> <index_code>
# Example: ./sample_import_script.sh standardized_nifty50.csv NIFTY50

set -e  # Exit on error

# Configuration
DB_FILE="${DB_FILE:-market_data.db}"
STAGING_TABLE="staging_constituents"
MANIFEST_DIR="./manifests"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate inputs
if [ $# -lt 2 ]; then
    log_error "Usage: $0 <csv_file> <index_code>"
    log_error "Example: $0 standardized_nifty50.csv NIFTY50"
    exit 1
fi

CSV_FILE="$1"
INDEX_CODE="$2"

# Validate CSV file exists
if [ ! -f "$CSV_FILE" ]; then
    log_error "CSV file not found: $CSV_FILE"
    exit 1
fi

# Validate database file exists
if [ ! -f "$DB_FILE" ]; then
    log_error "Database file not found: $DB_FILE"
    log_error "Run: sqlite3 $DB_FILE < nse_indices_schema.sql"
    exit 1
fi

# Create manifest directory
mkdir -p "$MANIFEST_DIR"

# Get file hash
FILE_HASH=$(sha256sum "$CSV_FILE" | awk '{print $1}')
log_info "File hash: $FILE_HASH"

# Get timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
log_info "Import timestamp: $TIMESTAMP"

# Count rows in CSV (excluding header)
ROWS_EXPECTED=$(($(wc -l < "$CSV_FILE") - 1))
log_info "Expected rows: $ROWS_EXPECTED"

# Step 1: Create staging table
log_info "Creating staging table..."
sqlite3 "$DB_FILE" <<'SQL'
DROP TABLE IF EXISTS staging_constituents;

CREATE TABLE staging_constituents (
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

# Step 2: Import CSV into staging
log_info "Importing CSV into staging table..."
sqlite3 "$DB_FILE" <<SQL
.mode csv
.separator ","
.import $CSV_FILE $STAGING_TABLE
SQL

# Remove header row if it was imported as data
sqlite3 "$DB_FILE" <<SQL
DELETE FROM staging_constituents 
WHERE index_code = 'index_code' OR symbol = 'symbol';
SQL

# Step 3: Get row count after import
ROWS_STAGED=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM staging_constituents;")
log_info "Rows staged: $ROWS_STAGED"

# Step 4: Validate and resolve ISINs
log_info "Validating ISINs..."
MISSING_ISIN=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM staging_constituents WHERE isin IS NULL OR isin = '';")
log_warn "Rows with missing ISIN: $MISSING_ISIN"

# Calculate percentage of missing ISINs
if [ "$ROWS_STAGED" -gt 0 ]; then
    MISSING_PERCENT=$(awk "BEGIN {printf \"%.2f\", ($MISSING_ISIN / $ROWS_STAGED) * 100}")
    log_info "Missing ISIN percentage: $MISSING_PERCENT%"
    
    # Check threshold (0.5%)
    if (( $(echo "$MISSING_PERCENT > 0.5" | bc -l) )); then
        log_error "Missing ISIN percentage exceeds threshold (0.5%)"
        log_error "Import aborted. Please review and fix ISIN data."
        exit 1
    fi
fi

# Step 5: Insert index metadata
log_info "Inserting index metadata..."
sqlite3 "$DB_FILE" <<SQL
INSERT OR IGNORE INTO indices (index_code, index_name, index_type, source_url, last_updated)
SELECT DISTINCT 
    index_code,
    index_name,
    index_type,
    source_file_name,
    '$TIMESTAMP'
FROM staging_constituents
WHERE index_code IS NOT NULL;
SQL

# Step 6: Upsert companies
log_info "Upserting companies..."
sqlite3 "$DB_FILE" <<SQL
INSERT OR IGNORE INTO companies (isin, symbol, company_name, listed_exchange)
SELECT DISTINCT 
    isin,
    symbol,
    company_name,
    'NSE'
FROM staging_constituents
WHERE isin IS NOT NULL AND isin != '';
SQL

# Step 7: Insert constituents
log_info "Linking constituents to indices..."
sqlite3 "$DB_FILE" <<SQL
BEGIN TRANSACTION;

INSERT INTO index_constituents (index_id, company_id, weight, effective_date, source_csv_url, raw_row_json)
SELECT 
    i.id,
    c.id,
    s.weight,
    s.effective_date,
    s.source_file_name,
    s.raw_row_json
FROM staging_constituents s
JOIN indices i ON i.index_code = s.index_code
JOIN companies c ON c.isin = s.isin
WHERE s.isin IS NOT NULL AND s.isin != '';

COMMIT;
SQL

# Step 8: Get import statistics
ROWS_IMPORTED=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM index_constituents WHERE source_csv_url = '$(basename "$CSV_FILE")';")
ROWS_FLAGGED=$MISSING_ISIN

log_info "Rows imported: $ROWS_IMPORTED"
log_info "Rows flagged: $ROWS_FLAGGED"

# Step 9: Create indexes if not exists
log_info "Creating indexes..."
sqlite3 "$DB_FILE" <<SQL
CREATE INDEX IF NOT EXISTS idx_companies_isin ON companies(isin);
CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol);
CREATE INDEX IF NOT EXISTS idx_indices_code ON indices(index_code);
CREATE INDEX IF NOT EXISTS idx_const_idx_comp ON index_constituents(index_id, company_id);
CREATE INDEX IF NOT EXISTS idx_const_effective_date ON index_constituents(effective_date);
SQL

# Step 10: Run ANALYZE
log_info "Analyzing database..."
sqlite3 "$DB_FILE" "ANALYZE;"

# Step 11: Generate manifest
MANIFEST_FILE="$MANIFEST_DIR/manifest_${INDEX_CODE}_$(date +%Y%m%d_%H%M%S).json"
log_info "Generating manifest: $MANIFEST_FILE"

# Get error details for flagged rows
ERRORS=$(sqlite3 "$DB_FILE" <<SQL
SELECT json_group_array(
    json_object(
        'symbol', symbol,
        'company_name', company_name,
        'issue', 'Missing ISIN'
    )
)
FROM staging_constituents
WHERE isin IS NULL OR isin = ''
LIMIT 100;
SQL
)

# Calculate row delta if previous import exists
PREVIOUS_COUNT=$(sqlite3 "$DB_FILE" <<SQL
SELECT COUNT(*) FROM index_constituents ic
JOIN indices i ON i.id = ic.index_id
WHERE i.index_code = '$INDEX_CODE'
AND ic.id NOT IN (
    SELECT id FROM index_constituents 
    WHERE source_csv_url = '$(basename "$CSV_FILE")'
);
SQL
)

ROW_COUNT_DELTA=0
if [ "$PREVIOUS_COUNT" -gt 0 ]; then
    ROW_COUNT_DELTA=$(awk "BEGIN {printf \"%.2f\", abs(($ROWS_IMPORTED - $PREVIOUS_COUNT) / $PREVIOUS_COUNT) * 100}")
fi

# Create manifest JSON
cat > "$MANIFEST_FILE" <<JSON
{
  "source_url": "manual_import",
  "source_file_name": "$(basename "$CSV_FILE")",
  "file_hash": "$FILE_HASH",
  "download_timestamp": "$TIMESTAMP",
  "rows_expected": $ROWS_EXPECTED,
  "rows_imported": $ROWS_IMPORTED,
  "rows_flagged": $ROWS_FLAGGED,
  "errors": $ERRORS,
  "pdf_version": null,
  "isin_unresolved_count": $MISSING_ISIN,
  "row_count_delta_percent": $ROW_COUNT_DELTA
}
JSON

# Step 12: Insert manifest into database
log_info "Recording manifest in database..."
sqlite3 "$DB_FILE" <<SQL
INSERT INTO import_manifest (
    source_url, 
    source_file_name, 
    file_hash, 
    download_timestamp,
    rows_expected,
    rows_imported,
    rows_flagged,
    errors_json
)
VALUES (
    'manual_import',
    '$(basename "$CSV_FILE")',
    '$FILE_HASH',
    '$TIMESTAMP',
    $ROWS_EXPECTED,
    $ROWS_IMPORTED,
    $ROWS_FLAGGED,
    '$ERRORS'
);
SQL

# Step 13: Cleanup staging table (optional)
log_info "Cleaning up staging table..."
sqlite3 "$DB_FILE" "DROP TABLE IF EXISTS staging_constituents;"

# Summary
echo ""
log_info "═══════════════════════════════════════════════"
log_info "Import completed successfully!"
log_info "═══════════════════════════════════════════════"
log_info "Index: $INDEX_CODE"
log_info "CSV File: $CSV_FILE"
log_info "Rows Expected: $ROWS_EXPECTED"
log_info "Rows Imported: $ROWS_IMPORTED"
log_info "Rows Flagged: $ROWS_FLAGGED"
log_info "Manifest: $MANIFEST_FILE"
log_info "═══════════════════════════════════════════════"

# Verification query
echo ""
log_info "Running verification query..."
sqlite3 "$DB_FILE" <<SQL
SELECT 
    i.index_code,
    i.index_name,
    COUNT(ic.id) as constituents,
    ROUND(SUM(ic.weight), 2) as total_weight
FROM indices i
LEFT JOIN index_constituents ic ON ic.index_id = i.id
WHERE i.index_code = '$INDEX_CODE'
GROUP BY i.index_code, i.index_name;
SQL

echo ""
log_info "Import process complete!"
