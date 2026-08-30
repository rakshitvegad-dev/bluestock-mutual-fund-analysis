"""
Bluestock Mutual Fund Analytics - NAV History Cleaning

Cleans the raw NAV history dataset by:
- parsing transaction dates,
- sorting records by fund and date,
- forward-filling NAV values within each fund,
- removing duplicate records,
- removing invalid NAV values.

Input:
    data/raw/nav_history.csv

Output:
    data/processed/nav_history_cleaned.csv
"""

from pathlib import Path
import sys
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "raw" / "nav_history.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "nav_history_cleaned.csv"


def clean_nav_history(input_file: Path, output_file: Path) -> None:
    """Clean NAV history data and save the processed dataset."""

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {input_file}"
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_file)

    original_shape = df.shape

    required_columns = {"date", "amfi_code", "nav"}

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df = df.sort_values(
        ["amfi_code", "date"]
    )

    df["nav"] = (
        df.groupby("amfi_code")["nav"]
        .ffill()
    )

    df = df.drop_duplicates()

    df = df[df["nav"] > 0]

    df.to_csv(
        output_file,
        index=False
    )

    print("=" * 70)
    print("NAV HISTORY CLEANING")
    print("=" * 70)
    print(f"Input file:       {input_file}")
    print(f"Original shape:   {original_shape}")
    print(f"Cleaned shape:    {df.shape}")
    print(f"Rows removed:     {original_shape[0] - df.shape[0]}")
    print(f"Output file:      {output_file}")
    print("=" * 70)
    print("NAV history cleaned successfully.")


def main() -> None:
    """Run the NAV history cleaning workflow."""

    try:
        clean_nav_history(
            INPUT_FILE,
            OUTPUT_FILE
        )
    except Exception as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
