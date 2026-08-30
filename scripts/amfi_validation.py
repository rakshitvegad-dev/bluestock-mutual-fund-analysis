"""
Bluestock Mutual Fund Analytics - AMFI Code Validation

Validates that every AMFI code present in fund_master.csv also exists
in nav_history.csv.

Input:
    data/raw/fund_master.csv
    data/raw/nav_history.csv

Validation:
    Checks for AMFI codes present in fund_master but missing from
    nav_history.
"""

from pathlib import Path
import sys
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

FUND_MASTER_FILE = (
    BASE_DIR / "data" / "raw" / "fund_master.csv"
)

NAV_HISTORY_FILE = (
    BASE_DIR / "data" / "raw" / "nav_history.csv"
)


def validate_amfi_codes(
    fund_master_file: Path,
    nav_history_file: Path,
) -> bool:
    """Validate AMFI code coverage between fund master and NAV history."""

    if not fund_master_file.exists():
        raise FileNotFoundError(
            f"Fund master file not found: {fund_master_file}"
        )

    if not nav_history_file.exists():
        raise FileNotFoundError(
            f"NAV history file not found: {nav_history_file}"
        )

    fund_master = pd.read_csv(fund_master_file)
    nav_history = pd.read_csv(nav_history_file)

    required_fund_columns = {"amfi_code"}
    required_nav_columns = {"amfi_code"}

    missing_fund_columns = (
        required_fund_columns - set(fund_master.columns)
    )

    missing_nav_columns = (
        required_nav_columns - set(nav_history.columns)
    )

    if missing_fund_columns:
        raise ValueError(
            "Missing required columns in fund_master.csv: "
            f"{sorted(missing_fund_columns)}"
        )

    if missing_nav_columns:
        raise ValueError(
            "Missing required columns in nav_history.csv: "
            f"{sorted(missing_nav_columns)}"
        )

    fund_codes = set(
        fund_master["amfi_code"].dropna()
    )

    nav_codes = set(
        nav_history["amfi_code"].dropna()
    )

    missing_codes = fund_codes - nav_codes

    print("=" * 70)
    print("AMFI CODE VALIDATION")
    print("=" * 70)
    print(f"Fund master AMFI codes: {len(fund_codes)}")
    print(f"NAV history AMFI codes: {len(nav_codes)}")
    print(f"Missing AMFI codes:     {len(missing_codes)}")

    if not missing_codes:
        print("\nSUCCESS: All AMFI codes in fund_master exist in nav_history.")
        print("=" * 70)
        return True

    print("\nWARNING: Some AMFI codes are missing from nav_history.")

    for code in sorted(missing_codes):
        print(f"  - {code}")

    print("=" * 70)

    return False


def main() -> None:
    """Run AMFI code validation."""

    try:
        validation_passed = validate_amfi_codes(
            FUND_MASTER_FILE,
            NAV_HISTORY_FILE,
        )

        if not validation_passed:
            sys.exit(1)

    except Exception as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
