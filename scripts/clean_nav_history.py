"""
Bluestock Mutual Fund Analytics - NAV History Cleaning

Cleans the raw NAV history dataset by:
- parsing dates,
- sorting records by fund and date,
- forward-filling NAV values within each fund,
- removing duplicate records,
- removing invalid NAV values,
- safely writing the processed CSV.

Input:
    data/raw/nav_history.csv

Output:
    data/processed/nav_history_cleaned.csv
"""

from pathlib import Path
import sys
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "nav_history.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "nav_history_cleaned.csv"
)


# ============================================================
# CLEAN NAV HISTORY
# ============================================================

def clean_nav_history(
    input_file: Path,
    output_file: Path
) -> None:

    print("=" * 70)
    print("NAV HISTORY CLEANING")
    print("=" * 70)

    # --------------------------------------------------------
    # Check input
    # --------------------------------------------------------

    if not input_file.exists():

        raise FileNotFoundError(
            f"Input dataset not found:\n{input_file}"
        )

    print(f"Input file:       {input_file}")

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    output_dir = output_file.parent

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    print(f"Output directory: {output_dir}")

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = pd.read_csv(
        input_file
    )

    original_rows = len(df)

    print(
        f"Original rows:    {original_rows:,}"
    )

    # --------------------------------------------------------
    # Validate columns
    # --------------------------------------------------------

    required_columns = {
        "date",
        "amfi_code",
        "nav"
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    # --------------------------------------------------------
    # Parse dates
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    invalid_dates = df["date"].isna().sum()

    if invalid_dates > 0:

        print(
            f"Invalid dates removed: {invalid_dates:,}"
        )

        df = df.dropna(
            subset=["date"]
        )

    # --------------------------------------------------------
    # Convert NAV to numeric
    # --------------------------------------------------------

    df["nav"] = pd.to_numeric(
        df["nav"],
        errors="coerce"
    )

    invalid_nav = (
        df["nav"].isna()
        | (df["nav"] <= 0)
    ).sum()

    if invalid_nav > 0:

        print(
            f"Invalid NAV rows removed: "
            f"{invalid_nav:,}"
        )

        df = df[
            df["nav"].notna()
            & (df["nav"] > 0)
        ]

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    df = df.sort_values(
        ["amfi_code", "date"]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Remove duplicate fund/date records
    # --------------------------------------------------------

    duplicates = df.duplicated(
        subset=["amfi_code", "date"]
    ).sum()

    if duplicates > 0:

        print(
            f"Duplicate fund/date rows removed: "
            f"{duplicates:,}"
        )

        df = df.drop_duplicates(
            subset=["amfi_code", "date"],
            keep="last"
        )

    # --------------------------------------------------------
    # Forward-fill NAV within each fund
    # --------------------------------------------------------

    df["nav"] = (
        df.groupby(
            "amfi_code"
        )["nav"]
        .ffill()
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    if df["nav"].isna().any():

        raise ValueError(
            "NAV column still contains NULL values "
            "after forward-fill."
        )

    if (df["nav"] <= 0).any():

        raise ValueError(
            "NAV column contains values <= 0."
        )

    # --------------------------------------------------------
    # Final sort
    # --------------------------------------------------------

    df = df.sort_values(
        ["amfi_code", "date"]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Save safely
    # --------------------------------------------------------

    temp_file = output_dir / (
        "nav_history_cleaned_tmp.csv"
    )

    # Remove old temporary file if present

    if temp_file.exists():

        temp_file.unlink()

    print(
        f"Writing processed file:\n{output_file}"
    )

    df.to_csv(
        temp_file,
        index=False,
        encoding="utf-8"
    )

    # Replace existing output

    if output_file.exists():

        output_file.unlink()

    temp_file.replace(
        output_file
    )

    # --------------------------------------------------------
    # Final statistics
    # --------------------------------------------------------

    cleaned_rows = len(df)

    rows_removed = (
        original_rows
        - cleaned_rows
    )

    print()
    print(
        f"Cleaned rows:     {cleaned_rows:,}"
    )

    print(
        f"Rows removed:     {rows_removed:,}"
    )

    print(
        f"Unique funds:     "
        f"{df['amfi_code'].nunique():,}"
    )

    print(
        f"Date range:       "
        f"{df['date'].min().date()} "
        f"to "
        f"{df['date'].max().date()}"
    )

    print(
        f"Output file:      {output_file}"
    )

    print(
        f"Output size:      "
        f"{output_file.stat().st_size:,} bytes"
    )

    print("=" * 70)
    print(
        "NAV history cleaned successfully."
    )
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    try:

        clean_nav_history(
            INPUT_FILE,
            OUTPUT_FILE
        )

    except Exception as error:

        print()
        print("=" * 70)
        print("NAV HISTORY CLEANING FAILED")
        print("=" * 70)
        print(
            f"ERROR: {error}"
        )
        print("=" * 70)

        sys.exit(1)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()