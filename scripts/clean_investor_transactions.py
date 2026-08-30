"""
Bluestock Mutual Fund Analytics - Investor Transaction Cleaning

Cleans the raw investor transaction dataset by:
- validating required columns,
- standardizing transaction types,
- converting transaction amounts to numeric values,
- standardizing KYC status values,
- converting transaction dates,
- removing duplicate records.

Input:
    data/raw/investor_transactions.csv

Output:
    data/processed/investor_transactions_cleaned.csv
"""

from pathlib import Path
import sys
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "raw" / "investor_transactions.csv"
OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "investor_transactions_cleaned.csv"
)


REQUIRED_COLUMNS = {
    "investor_id",
    "transaction_date",
    "amfi_code",
    "transaction_type",
    "amount_inr",
    "kyc_status",
}


VALID_KYC_STATUS = {
    "Verified",
    "Pending",
    "Rejected",
}


TRANSACTION_TYPE_MAP = {
    "Sip": "SIP",
    "Lump Sum": "Lumpsum",
    "Lumpsum": "Lumpsum",
    "Redeem": "Redemption",
    "Redemption": "Redemption",
}


def clean_investor_transactions(
    input_file: Path,
    output_file: Path,
) -> None:
    """Clean investor transaction records and save the result."""

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {input_file}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_csv(input_file)

    original_shape = df.shape

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    # Convert transaction date.
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce",
    )

    # Standardize transaction type.
    df["transaction_type"] = (
        df["transaction_type"]
        .astype(str)
        .str.strip()
        .str.title()
        .replace(TRANSACTION_TYPE_MAP)
    )

    # Convert transaction amount to numeric.
    df["amount_inr"] = pd.to_numeric(
        df["amount_inr"],
        errors="coerce",
    )

    # Standardize KYC status.
    df["kyc_status"] = (
        df["kyc_status"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    df["kyc_status"] = df["kyc_status"].where(
        df["kyc_status"].isin(VALID_KYC_STATUS),
        "Unknown",
    )

    # Remove duplicate records.
    duplicate_count = int(df.duplicated().sum())
    df = df.drop_duplicates()

    # Remove rows with invalid transaction amounts.
    invalid_amount_count = int(
        (df["amount_inr"].isna() | (df["amount_inr"] <= 0)).sum()
    )

    df = df[
        df["amount_inr"].notna()
        & (df["amount_inr"] > 0)
    ]

    # Remove rows with invalid transaction dates.
    invalid_date_count = int(
        df["transaction_date"].isna().sum()
    )

    df = df[df["transaction_date"].notna()]

    df.to_csv(
        output_file,
        index=False,
    )

    print("=" * 70)
    print("INVESTOR TRANSACTION CLEANING")
    print("=" * 70)
    print(f"Input file:              {input_file}")
    print(f"Original shape:          {original_shape}")
    print(f"Duplicate rows removed:  {duplicate_count}")
    print(f"Invalid amounts removed: {invalid_amount_count}")
    print(f"Invalid dates removed:   {invalid_date_count}")
    print(f"Cleaned shape:           {df.shape}")
    print(f"Output file:             {output_file}")
    print("=" * 70)
    print("Investor transactions cleaned successfully.")


def main() -> None:
    """Run the investor transaction cleaning workflow."""

    try:
        clean_investor_transactions(
            INPUT_FILE,
            OUTPUT_FILE,
        )
    except Exception as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
