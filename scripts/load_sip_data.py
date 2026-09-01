import sqlite3
import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "bluestock_mf.db"
SIP_PATH = BASE_DIR / "data" / "raw" / "monthly_sip_inflows.csv"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("LOADING MONTHLY SIP INFLOW DATA")
    print("=" * 70)

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    if not SIP_PATH.exists():
        raise FileNotFoundError(
            f"SIP dataset not found:\n{SIP_PATH}"
        )

    print(f"\nDatabase : {DB_PATH}")
    print(f"SIP file : {SIP_PATH}")

    # --------------------------------------------------------
    # Read CSV
    # --------------------------------------------------------

    df = pd.read_csv(SIP_PATH)

    print(f"\nSource rows: {len(df):,}")

    print("\nColumns:")
    for column in df.columns:
        print(f"  - {column}")

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "month",
        "sip_inflow_crore",
        "active_sip_accounts_crore",
        "new_sip_accounts_lakh",
        "sip_aum_lakh_crore",
        "yoy_growth_pct"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns:\n"
            + str(missing_columns)
        )

    df = df[required_columns].copy()

    # --------------------------------------------------------
    # Convert month
    # --------------------------------------------------------

    df["month"] = pd.to_datetime(
        df["month"],
        format="%Y-%m",
        errors="coerce"
    )

    invalid_months = df["month"].isna().sum()

    print(
        f"\nInvalid month values: {invalid_months}"
    )

    if invalid_months > 0:
        raise ValueError(
            "Invalid month values found."
        )

    # --------------------------------------------------------
    # Numeric validation
    # --------------------------------------------------------

    numeric_columns = [
        "sip_inflow_crore",
        "active_sip_accounts_crore",
        "new_sip_accounts_lakh",
        "sip_aum_lakh_crore",
        "yoy_growth_pct"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    print("\nNULL counts:")
    print(df.isna().sum())

    # --------------------------------------------------------
    # Validate SIP inflow
    # --------------------------------------------------------

    invalid_inflow = (
        df["sip_inflow_crore"] <= 0
    ).sum()

    print(
        f"\nSIP inflow > 0 validation: "
        f"{'PASS' if invalid_inflow == 0 else 'FAIL'} "
        f"Invalid rows={invalid_inflow}"
    )

    if invalid_inflow > 0:
        raise ValueError(
            "Invalid SIP inflow values found."
        )

    # --------------------------------------------------------
    # Connect database
    # --------------------------------------------------------

    conn = sqlite3.connect(DB_PATH)

    try:

        # ----------------------------------------------------
        # Enable foreign keys
        # ----------------------------------------------------

        conn.execute(
            "PRAGMA foreign_keys = ON"
        )

        # ----------------------------------------------------
        # Create SIP table
        # ----------------------------------------------------

        print("\nCreating monthly_sip_inflow table...")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS monthly_sip_inflow (

                sip_key INTEGER PRIMARY KEY AUTOINCREMENT,

                month TEXT NOT NULL UNIQUE,

                sip_inflow_crore REAL NOT NULL,

                active_sip_accounts_crore REAL,

                new_sip_accounts_lakh REAL,

                sip_aum_lakh_crore REAL,

                yoy_growth_pct REAL
            )
            """
        )

        # ----------------------------------------------------
        # Clear old SIP data
        # ----------------------------------------------------

        conn.execute(
            "DELETE FROM monthly_sip_inflow"
        )

        # ----------------------------------------------------
        # Insert data
        # ----------------------------------------------------

        for _, row in df.iterrows():

            conn.execute(
                """
                INSERT INTO monthly_sip_inflow (
                    month,
                    sip_inflow_crore,
                    active_sip_accounts_crore,
                    new_sip_accounts_lakh,
                    sip_aum_lakh_crore,
                    yoy_growth_pct
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["month"].strftime("%Y-%m-%d"),

                    float(row["sip_inflow_crore"]),

                    None
                    if pd.isna(
                        row["active_sip_accounts_crore"]
                    )
                    else float(
                        row["active_sip_accounts_crore"]
                    ),

                    None
                    if pd.isna(
                        row["new_sip_accounts_lakh"]
                    )
                    else float(
                        row["new_sip_accounts_lakh"]
                    ),

                    None
                    if pd.isna(
                        row["sip_aum_lakh_crore"]
                    )
                    else float(
                        row["sip_aum_lakh_crore"]
                    ),

                    None
                    if pd.isna(
                        row["yoy_growth_pct"]
                    )
                    else float(
                        row["yoy_growth_pct"]
                    )
                )
            )

        # ----------------------------------------------------
        # Commit
        # ----------------------------------------------------

        conn.commit()

        print(
            f"\nmonthly_sip_inflow loaded: "
            f"{len(df):,} rows"
        )

        # ----------------------------------------------------
        # Verify
        # ----------------------------------------------------

        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM monthly_sip_inflow
            """
        ).fetchone()[0]

        print(
            f"Database rows: {count:,}"
        )

        # ----------------------------------------------------
        # Date range
        # ----------------------------------------------------

        date_range = conn.execute(
            """
            SELECT
                MIN(month),
                MAX(month)
            FROM monthly_sip_inflow
            """
        ).fetchone()

        print(
            f"Date range: "
            f"{date_range[0]} → {date_range[1]}"
        )

        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        print("\n" + "=" * 70)
        print("SIP DATA LOADING COMPLETED SUCCESSFULLY")
        print("=" * 70)

    except Exception as e:

        conn.rollback()

        print("\n" + "=" * 70)
        print("SIP DATA LOADING FAILED")
        print("=" * 70)

        print(f"Error: {e}")

        raise

    finally:

        conn.close()

        print("\nDatabase connection closed.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()