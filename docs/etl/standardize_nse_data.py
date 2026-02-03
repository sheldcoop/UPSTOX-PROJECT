#!/usr/bin/env python3
"""
NSE Indices Data Standardization Script
Purpose: Convert raw NSE CSV files to standardized format for ETL import
Usage: python standardize_nse_data.py <input_csv> <index_code> <index_type>
Example: python standardize_nse_data.py nifty50_raw.csv NIFTY50 broad
"""

import sys
import pandas as pd
import json
import hashlib
from datetime import datetime
from pathlib import Path


def calculate_file_hash(filepath):
    """Calculate SHA256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def normalize_weight(weight_value):
    """Normalize weight field by removing % and converting to float."""
    if pd.isna(weight_value):
        return None

    weight_str = str(weight_value).strip()
    # Remove % sign if present
    weight_str = weight_str.replace("%", "").replace(",", "")

    try:
        return float(weight_str)
    except ValueError:
        return None


def normalize_market_cap(market_cap_value):
    """
    Normalize market cap by converting lakhs/crores to plain numeric.
    Examples: "10.5 Cr" -> 105000000, "500 Lakhs" -> 50000000
    """
    if pd.isna(market_cap_value):
        return None

    cap_str = str(market_cap_value).strip().replace(",", "")

    # Check for crore/cr suffix
    if "cr" in cap_str.lower():
        numeric_part = float(
            cap_str.lower().replace("cr", "").replace("crore", "").strip()
        )
        return numeric_part * 10000000  # 1 crore = 10 million

    # Check for lakh/lac suffix
    if "la" in cap_str.lower():
        numeric_part = float(
            cap_str.lower().replace("lakh", "").replace("lac", "").strip()
        )
        return numeric_part * 100000  # 1 lakh = 100 thousand

    # Try direct conversion
    try:
        return float(cap_str)
    except ValueError:
        return None


def normalize_date(date_value):
    """Convert date to ISO-8601 format (YYYY-MM-DD)."""
    if pd.isna(date_value):
        return datetime.now().strftime("%Y-%m-%d")

    try:
        # Try parsing various date formats
        date_obj = pd.to_datetime(date_value, dayfirst=True)
        return date_obj.strftime("%Y-%m-%d")
    except:
        return datetime.now().strftime("%Y-%m-%d")


def standardize_nse_data(input_csv, index_code, index_type, output_csv=None):
    """
    Standardize NSE constituent data CSV.

    Args:
        input_csv: Path to raw CSV file
        index_code: Index code (e.g., 'NIFTY50')
        index_type: Index type (e.g., 'broad', 'sector', 'thematic')
        output_csv: Optional output path (defaults to standardized_<input>)
    """
    print(f"Reading raw CSV: {input_csv}")
    df = pd.read_csv(input_csv)

    print(f"Original columns: {list(df.columns)}")
    print(f"Original rows: {len(df)}")

    # Column mapping - adjust based on actual CSV structure
    column_mapping = {
        # Try various possible column names
        "Index Name": "index_name",
        "Index": "index_name",
        "Company Name": "company_name",
        "Name": "company_name",
        "Issuer": "company_name",
        "Symbol": "symbol",
        "Ticker": "symbol",
        "Trading Symbol": "symbol",
        "ISIN": "isin",
        "ISIN Code": "isin",
        "ISIN No": "isin",
        "Weight": "weight",
        "Index Weight": "weight",
        "% Weight": "weight",
        "Market Cap": "market_cap",
        "Mkt Cap": "market_cap",
        "Market Capitalisation": "market_cap",
        "Free Float": "free_float_factor",
        "Free Float Factor": "free_float_factor",
        "Date": "effective_date",
        "Effective Date": "effective_date",
        "As On": "effective_date",
    }

    # Rename columns based on mapping
    df = df.rename(columns=column_mapping)

    # Create standardized dataframe
    standardized_df = pd.DataFrame()

    # Required fields
    standardized_df["index_code"] = index_code
    standardized_df["index_name"] = df.get(
        "index_name", index_code.replace("_", " ").title()
    )
    standardized_df["index_type"] = index_type

    # Company identification
    standardized_df["company_name"] = df["company_name"] if "company_name" in df else ""
    standardized_df["symbol"] = df["symbol"] if "symbol" in df else ""
    standardized_df["isin"] = df["isin"] if "isin" in df else ""

    # Numeric fields - apply normalization
    if "weight" in df:
        standardized_df["weight"] = df["weight"].apply(normalize_weight)
    else:
        standardized_df["weight"] = None

    if "market_cap" in df:
        standardized_df["market_cap"] = df["market_cap"].apply(normalize_market_cap)
    else:
        standardized_df["market_cap"] = None

    if "free_float_factor" in df:
        standardized_df["free_float_factor"] = df["free_float_factor"].apply(
            normalize_weight
        )
    else:
        standardized_df["free_float_factor"] = None

    # Date field
    if "effective_date" in df:
        standardized_df["effective_date"] = df["effective_date"].apply(normalize_date)
    else:
        standardized_df["effective_date"] = datetime.now().strftime("%Y-%m-%d")

    # Metadata
    standardized_df["source_file_name"] = Path(input_csv).name

    # Store raw row as JSON for audit trail
    standardized_df["raw_row_json"] = df.apply(
        lambda x: json.dumps(x.to_dict()), axis=1
    )

    # Remove rows with missing critical data
    print(f"\nValidating data...")
    initial_rows = len(standardized_df)

    # Flag rows missing ISIN
    missing_isin = standardized_df["isin"].isna() | (standardized_df["isin"] == "")
    if missing_isin.any():
        print(f"WARNING: {missing_isin.sum()} rows missing ISIN")
        print(standardized_df[missing_isin][["symbol", "company_name"]].head())

    # Calculate statistics
    print(f"\nStandardization complete:")
    print(f"  Input rows: {initial_rows}")
    print(f"  Output rows: {len(standardized_df)}")
    print(
        f"  Missing ISIN: {missing_isin.sum()} ({missing_isin.sum()/len(standardized_df)*100:.2f}%)"
    )

    if "weight" in standardized_df:
        total_weight = standardized_df["weight"].sum()
        print(f"  Total weight: {total_weight:.2f}%")

    # Save to output CSV
    if output_csv is None:
        output_csv = f"standardized_{Path(input_csv).name}"

    print(f"\nSaving to: {output_csv}")
    standardized_df.to_csv(output_csv, index=False)

    # Calculate file hash
    file_hash = calculate_file_hash(output_csv)

    # Create manifest
    manifest = {
        "source_url": "manual_import",
        "source_file_name": Path(input_csv).name,
        "file_hash": file_hash,
        "download_timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rows_expected": len(df),
        "rows_imported": 0,  # Will be updated after actual import
        "rows_flagged": int(missing_isin.sum()),
        "errors": [],
        "pdf_version": None,
        "isin_unresolved_count": int(missing_isin.sum()),
        "row_count_delta_percent": 0.0,
    }

    manifest_file = output_csv.replace(".csv", "_manifest.json")
    print(f"Saving manifest to: {manifest_file}")
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n✓ Standardization complete!")
    print(
        f"✓ Ready for import using: ./sample_import_script.sh {output_csv} {index_code}"
    )

    return output_csv


def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print(
            "Usage: python standardize_nse_data.py <input_csv> <index_code> <index_type>"
        )
        print("Example: python standardize_nse_data.py nifty50_raw.csv NIFTY50 broad")
        print(
            "\nValid index types: broad, sector, thematic, strategy, blended, multi-asset"
        )
        sys.exit(1)

    input_csv = sys.argv[1]
    index_code = sys.argv[2]
    index_type = sys.argv[3]

    if not Path(input_csv).exists():
        print(f"ERROR: File not found: {input_csv}")
        sys.exit(1)

    valid_types = ["broad", "sector", "thematic", "strategy", "blended", "multi-asset"]
    if index_type not in valid_types:
        print(f"WARNING: '{index_type}' is not a standard index type")
        print(f"Valid types: {', '.join(valid_types)}")

    standardize_nse_data(input_csv, index_code, index_type)


if __name__ == "__main__":
    main()
