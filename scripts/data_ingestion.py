"""
Bluestock Mutual Fund Analytics - Data Ingestion

Scans the project's data/raw directory, loads each CSV file, and reports
basic dataset information including shape, data types, missing values,
and duplicate rows.

Run from the project root:

    python scripts/data_ingestion.py
"""

from pathlib import Path
import sys
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FOLDER = BASE_DIR / "data" / "raw"


def inspect_csv(file_path: Path) -> None:
    """Load and display basic information for one CSV file."""

    print("\n" + "=" * 80)
    print(f"File: {file_path.name}")
    print("=" * 80)

    try:
        df = pd.read_csv(file_path)

        print("\nShape:")
        print(df.shape)

        print("\nData Types:")
        print(df.dtypes)

        print("\nFirst 5 Rows:")
        print(df.head())

        print("\nMissing Values:")
        print(df.isnull().sum())

        print("\nDuplicate Rows:")
        print(df.duplicated().sum())

    except Exception as error:
        print(f"\nERROR reading {file_path.name}:")
        print(error)
        raise


def main() -> None:
    """Run the data-ingestion inspection workflow."""

    print("=" * 80)
    print("BLUESTOCK MUTUAL FUND ANALYTICS")
    print("DATA INGESTION")
    print("=" * 80)

    print(f"Data folder: {DATA_FOLDER}")

    if not DATA_FOLDER.exists():
        print(f"\nERROR: Data folder not found: {DATA_FOLDER}")
        sys.exit(1)

    csv_files = sorted(DATA_FOLDER.glob("*.csv"))

    if not csv_files:
        print("\nERROR: No CSV files found in data/raw.")
        sys.exit(1)

    print(f"\nFound {len(csv_files)} CSV file(s)")

    for file_path in csv_files:
        inspect_csv(file_path)

    print("\n" + "=" * 80)
    print("DATA INGESTION COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
