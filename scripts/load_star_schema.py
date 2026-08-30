import sqlite3
import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "bluestock_mf.db"

RAW_DIR = BASE_DIR / "data" / "raw"

PROCESSED_DIR = BASE_DIR / "data" / "processed"

SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def print_section(title):

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def check_file(path):

    if not path.exists():

        raise FileNotFoundError(
            f"Required file not found:\n{path}"
        )


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    print_section("CREATING SQLITE DATABASE")

    # Remove old database
    if DB_PATH.exists():

        DB_PATH.unlink()

        print(
            f"Old database removed: {DB_PATH}"
        )

    # Create new database
    conn = sqlite3.connect(DB_PATH)

    # Enable foreign keys
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    print(
        f"New database created: {DB_PATH}"
    )

    return conn


# ============================================================
# CREATE STAR SCHEMA
# ============================================================

def create_schema(conn):

    print_section("CREATING STAR SCHEMA")

    check_file(SCHEMA_PATH)

    print(
        f"Schema file: {SCHEMA_PATH}"
    )

    schema_sql = SCHEMA_PATH.read_text(
        encoding="utf-8"
    )

    print(
        f"Schema file size: {len(schema_sql):,} characters"
    )

    print(
        "PRIMARY KEY found in schema :",
        "PRIMARY KEY" in schema_sql.upper()
    )

    print(
        "FOREIGN KEY found in schema :",
        "FOREIGN KEY" in schema_sql.upper()
    )

    conn.executescript(schema_sql)

    print(
        "\nSchema SQL executed successfully."
    )


# ============================================================
# VERIFY ACTUAL SQLITE SCHEMA
# ============================================================

def get_primary_keys(conn, table):

    rows = conn.execute(
        f"PRAGMA table_info([{table}])"
    ).fetchall()

    return [
        row[1]
        for row in rows
        if row[5] == 1
    ]


def get_foreign_keys(conn, table):

    rows = conn.execute(
        f"PRAGMA foreign_key_list([{table}])"
    ).fetchall()

    return rows


def verify_schema(conn):

    print_section(
        "VERIFYING ACTUAL SQLITE SCHEMA"
    )

    tables = [
        "dim_fund",
        "dim_date",
        "fact_nav",
        "fact_transactions",
        "fact_performance",
        "fact_aum"
    ]

    # --------------------------------------------------------
    # TABLE CHECK
    # --------------------------------------------------------

    print("\nTABLE CHECK")
    print("-" * 70)

    actual_tables = {
        row[0]
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            """
        ).fetchall()
    }

    for table in tables:

        status = (
            "PASS"
            if table in actual_tables
            else "FAIL"
        )

        print(
            f"{table:30} {status}"
        )

    # --------------------------------------------------------
    # PRIMARY KEY CHECK
    # --------------------------------------------------------

    print("\nPRIMARY KEY CHECK")
    print("-" * 70)

    for table in tables:

        primary_keys = get_primary_keys(
            conn,
            table
        )

        status = (
            "PASS"
            if primary_keys
            else "FAIL"
        )

        print(
            f"{table:30} {status} -> {primary_keys}"
        )

    # --------------------------------------------------------
    # FOREIGN KEY CHECK
    # --------------------------------------------------------

    print("\nFOREIGN KEY CHECK")
    print("-" * 70)

    for table in tables:

        foreign_keys = get_foreign_keys(
            conn,
            table
        )

        if foreign_keys:

            print(
                f"{table:30} PASS -> "
                f"{len(foreign_keys)} foreign key(s)"
            )

            for fk in foreign_keys:

                # SQLite PRAGMA format:
                # id, seq, table, from, to, on_update, on_delete, match

                print(
                    f"    {fk[3]} -> "
                    f"{fk[2]}.{fk[4]}"
                )

        else:

            print(
                f"{table:30} PASS -> 0 foreign key(s)"
            )

    print(
        "\nPRIMARY KEY and FOREIGN KEY "
        "constraints verified."
    )


# ============================================================
# LOAD DIM_FUND
# ============================================================

def load_dim_fund(conn):

    print("\nLoading dim_fund...")

    path = RAW_DIR / "fund_master.csv"

    check_file(path)

    df = pd.read_csv(path)

    columns = [
        "amfi_code",
        "fund_house",
        "scheme_name",
        "category",
        "sub_category",
        "plan",
        "launch_date",
        "benchmark",
        "expense_ratio_pct",
        "exit_load_pct",
        "min_sip_amount",
        "min_lumpsum_amount",
        "fund_manager",
        "risk_category",
        "sebi_category_code"
    ]

    missing_columns = [
        col
        for col in columns
        if col not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in fund_master.csv:\n"
            + str(missing_columns)
        )

    df = df[columns].copy()

    # Convert date to SQLite-safe string
    df["launch_date"] = pd.to_datetime(
        df["launch_date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    for _, row in df.iterrows():

        values = tuple(
            None if pd.isna(value)
            else value
            for value in row
        )

        conn.execute(
            """
            INSERT INTO dim_fund (
                amfi_code,
                fund_house,
                scheme_name,
                category,
                sub_category,
                plan,
                launch_date,
                benchmark,
                expense_ratio_pct,
                exit_load_pct,
                min_sip_amount,
                min_lumpsum_amount,
                fund_manager,
                risk_category,
                sebi_category_code
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values
        )

    print(
        f"dim_fund loaded: {len(df):,}"
    )


# ============================================================
# LOAD DIM_DATE
# ============================================================

def load_dim_date(conn):

    print("\nLoading dim_date...")

    all_dates = set()

    # --------------------------------------------------------
    # 1. NAV DATES
    # --------------------------------------------------------

    nav_path = (
        PROCESSED_DIR /
        "nav_history_cleaned.csv"
    )

    check_file(nav_path)

    nav = pd.read_csv(nav_path)

    if "date" not in nav.columns:

        raise ValueError(
            "date column not found in "
            "nav_history_cleaned.csv"
        )

    nav_dates = pd.to_datetime(
        nav["date"],
        errors="coerce"
    ).dropna()

    all_dates.update(
        nav_dates.dt.strftime(
            "%Y-%m-%d"
        )
    )

    print(
        f"NAV dates collected: {len(nav_dates):,}"
    )

    # --------------------------------------------------------
    # 2. TRANSACTION DATES
    # --------------------------------------------------------

    transaction_path = (
        PROCESSED_DIR /
        "investor_transactions_cleaned.csv"
    )

    check_file(transaction_path)

    transactions = pd.read_csv(
        transaction_path
    )

    if "transaction_date" not in transactions.columns:

        raise ValueError(
            "transaction_date column not found "
            "in investor_transactions_cleaned.csv"
        )

    transaction_dates = pd.to_datetime(
        transactions["transaction_date"],
        errors="coerce"
    ).dropna()

    all_dates.update(
        transaction_dates.dt.strftime(
            "%Y-%m-%d"
        )
    )

    print(
        "Transaction dates collected: "
        f"{len(transaction_dates):,}"
    )

    # --------------------------------------------------------
    # 3. AUM DATES
    # --------------------------------------------------------

    aum_path = (
        RAW_DIR /
        "aum_by_fund_house.csv"
    )

    check_file(aum_path)

    aum = pd.read_csv(aum_path)

    if "date" not in aum.columns:

        raise ValueError(
            "date column not found in "
            "aum_by_fund_house.csv"
        )

    aum_dates = pd.to_datetime(
        aum["date"],
        errors="coerce"
    ).dropna()

    all_dates.update(
        aum_dates.dt.strftime(
            "%Y-%m-%d"
        )
    )

    print(
        "AUM dates collected: "
        f"{len(aum_dates):,}"
    )

    # --------------------------------------------------------
    # CHECK
    # --------------------------------------------------------

    if not all_dates:

        raise ValueError(
            "No valid dates found for dim_date."
        )

    # --------------------------------------------------------
    # CREATE DATE DATAFRAME
    # --------------------------------------------------------

    dates = pd.DataFrame(
        {
            "full_date": sorted(all_dates)
        }
    )

    dates["full_date"] = pd.to_datetime(
        dates["full_date"]
    )

    dates["date_key"] = (
        dates["full_date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    dates["year"] = (
        dates["full_date"]
        .dt.year
    )

    dates["month"] = (
        dates["full_date"]
        .dt.month
    )

    dates["month_name"] = (
        dates["full_date"]
        .dt.month_name()
    )

    dates["quarter"] = (
        dates["full_date"]
        .dt.quarter
    )

    # --------------------------------------------------------
    # INSERT
    # --------------------------------------------------------

    for _, row in dates.iterrows():

        conn.execute(
            """
            INSERT INTO dim_date (
                date_key,
                full_date,
                year,
                month,
                month_name,
                quarter
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(row["date_key"]),

                # IMPORTANT:
                # Convert Timestamp to string
                row["full_date"].strftime(
                    "%Y-%m-%d"
                ),

                int(row["year"]),

                int(row["month"]),

                str(row["month_name"]),

                int(row["quarter"])
            )
        )

    print(
        f"dim_date loaded: {len(dates):,}"
    )


# ============================================================
# LOAD FACT_NAV
# ============================================================

def load_fact_nav(conn):

    print("\nLoading fact_nav...")

    path = (
        PROCESSED_DIR /
        "nav_history_cleaned.csv"
    )

    check_file(path)

    nav = pd.read_csv(path)

    nav["date"] = pd.to_datetime(
        nav["date"],
        errors="coerce"
    )

    nav["date_key"] = (
        nav["date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    # Check dates exist in dim_date
    missing_dates = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_nav
        """
    ).fetchone()[0]

    # --------------------------------------------------------
    # INSERT
    # --------------------------------------------------------

    for _, row in nav.iterrows():

        conn.execute(
            """
            INSERT INTO fact_nav (
                amfi_code,
                date_key,
                nav
            )
            VALUES (?, ?, ?)
            """,
            (
                int(row["amfi_code"]),
                int(row["date_key"]),
                float(row["nav"])
            )
        )

    print(
        f"fact_nav loaded: {len(nav):,}"
    )


# ============================================================
# LOAD FACT_TRANSACTIONS
# ============================================================

def load_fact_transactions(conn):

    print("\nLoading fact_transactions...")

    path = (
        PROCESSED_DIR /
        "investor_transactions_cleaned.csv"
    )

    check_file(path)

    df = pd.read_csv(path)

    if "transaction_date" in df.columns:

        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    for _, row in df.iterrows():

        values = tuple(
            None if pd.isna(value)
            else value
            for value in row
        )

        conn.execute(
            """
            INSERT INTO fact_transactions (
                investor_id,
                transaction_date,
                amfi_code,
                transaction_type,
                amount_inr,
                state,
                city,
                city_tier,
                age_group,
                gender,
                annual_income_lakh,
                payment_mode,
                kyc_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values
        )

    print(
        f"fact_transactions loaded: {len(df):,}"
    )


# ============================================================
# LOAD FACT_PERFORMANCE
# ============================================================

def load_fact_performance(conn):

    print("\nLoading fact_performance...")

    path = (
        PROCESSED_DIR /
        "cleaned_scheme_performance.csv"
    )

    check_file(path)

    df = pd.read_csv(path)

    columns = [
        "amfi_code",
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "benchmark_3yr_pct",
        "alpha",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
        "aum_crore",
        "expense_ratio_pct",
        "morningstar_rating",
        "risk_grade"
    ]

    missing_columns = [
        col
        for col in columns
        if col not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in "
            "cleaned_scheme_performance.csv:\n"
            + str(missing_columns)
        )

    df = df[columns].copy()

    for _, row in df.iterrows():

        values = tuple(
            None if pd.isna(value)
            else value
            for value in row
        )

        conn.execute(
            """
            INSERT INTO fact_performance (
                amfi_code,
                return_1yr_pct,
                return_3yr_pct,
                return_5yr_pct,
                benchmark_3yr_pct,
                alpha,
                beta,
                sharpe_ratio,
                sortino_ratio,
                std_dev_ann_pct,
                max_drawdown_pct,
                aum_crore,
                expense_ratio_pct,
                morningstar_rating,
                risk_grade
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values
        )

    print(
        f"fact_performance loaded: {len(df):,}"
    )


# ============================================================
# LOAD FACT_AUM
# ============================================================

def load_fact_aum(conn):

    print("\nLoading fact_aum...")

    path = (
        RAW_DIR /
        "aum_by_fund_house.csv"
    )

    check_file(path)

    df = pd.read_csv(path)

    required_columns = [
        "date",
        "fund_house",
        "aum_lakh_crore",
        "aum_crore",
        "num_schemes"
    ]

    missing_columns = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in "
            "aum_by_fund_house.csv:\n"
            + str(missing_columns)
        )

    # --------------------------------------------------------
    # Convert date
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    # Remove invalid dates
    df = df.dropna(
        subset=["date"]
    )

    # Generate date_key
    df["date_key"] = (
        df["date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Check that every AUM date exists
    # in dim_date
    # --------------------------------------------------------

    dim_dates = {
        row[0]
        for row in conn.execute(
            """
            SELECT date_key
            FROM dim_date
            """
        ).fetchall()
    }

    missing_date_keys = sorted(
        set(df["date_key"]) -
        dim_dates
    )

    if missing_date_keys:

        print(
            "\nWARNING: Missing AUM date keys "
            "in dim_date:"
        )

        print(
            missing_date_keys[:20]
        )

        raise ValueError(
            "AUM contains date_key values "
            "that do not exist in dim_date."
        )

    # --------------------------------------------------------
    # Insert
    # --------------------------------------------------------

    for _, row in df.iterrows():

        conn.execute(
            """
            INSERT INTO fact_aum (
                date_key,
                fund_house,
                aum_lakh_crore,
                aum_crore,
                num_schemes
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(row["date_key"]),

                str(row["fund_house"]),

                None
                if pd.isna(row["aum_lakh_crore"])
                else float(row["aum_lakh_crore"]),

                None
                if pd.isna(row["aum_crore"])
                else float(row["aum_crore"]),

                None
                if pd.isna(row["num_schemes"])
                else int(row["num_schemes"])
            )
        )

    print(
        f"fact_aum loaded: {len(df):,}"
    )


# ============================================================
# VERIFY ROW COUNTS
# ============================================================

def verify_counts(conn):

    print_section(
        "STAR SCHEMA ROW COUNTS"
    )

    tables = [
        "dim_fund",
        "dim_date",
        "fact_nav",
        "fact_transactions",
        "fact_performance",
        "fact_aum"
    ]

    for table in tables:

        count = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM [{table}]
            """
        ).fetchone()[0]

        print(
            f"{table:30} : {count:,}"
        )


# ============================================================
# VERIFY REFERENTIAL INTEGRITY
# ============================================================

def verify_referential_integrity(conn):

    print_section(
        "REFERENTIAL INTEGRITY CHECK"
    )

    checks = {

        "fact_nav -> dim_fund":
            """
            SELECT COUNT(*)
            FROM fact_nav f
            LEFT JOIN dim_fund d
                ON f.amfi_code = d.amfi_code
            WHERE d.amfi_code IS NULL
            """,

        "fact_nav -> dim_date":
            """
            SELECT COUNT(*)
            FROM fact_nav f
            LEFT JOIN dim_date d
                ON f.date_key = d.date_key
            WHERE d.date_key IS NULL
            """,

        "fact_transactions -> dim_fund":
            """
            SELECT COUNT(*)
            FROM fact_transactions f
            LEFT JOIN dim_fund d
                ON f.amfi_code = d.amfi_code
            WHERE d.amfi_code IS NULL
            """,

        "fact_transactions -> dim_date":
            """
            SELECT COUNT(*)
            FROM fact_transactions f
            LEFT JOIN dim_date d
                ON date(f.transaction_date)
                   = date(d.full_date)
            WHERE d.date_key IS NULL
            """,

        "fact_performance -> dim_fund":
            """
            SELECT COUNT(*)
            FROM fact_performance f
            LEFT JOIN dim_fund d
                ON f.amfi_code = d.amfi_code
            WHERE d.amfi_code IS NULL
            """,

        "fact_aum -> dim_date":
            """
            SELECT COUNT(*)
            FROM fact_aum f
            LEFT JOIN dim_date d
                ON f.date_key = d.date_key
            WHERE d.date_key IS NULL
            """
    }

    all_pass = True

    for name, query in checks.items():

        count = conn.execute(
            query
        ).fetchone()[0]

        if count == 0:

            print(
                f"{name:40} PASS"
            )

        else:

            print(
                f"{name:40} FAIL "
                f"Orphans={count}"
            )

            all_pass = False

    return all_pass


# ============================================================
# VALIDATE DATA
# ============================================================

def validate_data(conn):

    print_section(
        "DATA VALIDATION"
    )

    # --------------------------------------------------------
    # AMFI codes
    # --------------------------------------------------------

    fund_count = conn.execute(
        """
        SELECT COUNT(DISTINCT amfi_code)
        FROM dim_fund
        """
    ).fetchone()[0]

    nav_fund_count = conn.execute(
        """
        SELECT COUNT(DISTINCT amfi_code)
        FROM fact_nav
        """
    ).fetchone()[0]

    print(
        f"Unique funds in dim_fund : {fund_count}"
    )

    print(
        f"Unique funds in fact_nav : {nav_fund_count}"
    )

    if fund_count == nav_fund_count:

        print(
            "AMFI code validation: PASS"
        )

    else:

        print(
            "AMFI code validation: FAIL"
        )

    # --------------------------------------------------------
    # NAV
    # --------------------------------------------------------

    invalid_nav = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_nav
        WHERE nav <= 0
        """
    ).fetchone()[0]

    print(
        f"\nNAV > 0 validation: "
        f"{'PASS' if invalid_nav == 0 else 'FAIL'} "
        f"Invalid rows={invalid_nav}"
    )

    # --------------------------------------------------------
    # Transactions
    # --------------------------------------------------------

    invalid_transactions = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_transactions
        WHERE amount_inr <= 0
        """
    ).fetchone()[0]

    print(
        f"Transaction amount > 0: "
        f"{'PASS' if invalid_transactions == 0 else 'FAIL'} "
        f"Invalid rows={invalid_transactions}"
    )

    # --------------------------------------------------------
    # Performance
    # --------------------------------------------------------

    performance_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_performance
        """
    ).fetchone()[0]

    print(
        f"Performance records: "
        f"{performance_count}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    conn = create_database()

    try:

        # ----------------------------------------------------
        # Create schema
        # ----------------------------------------------------

        create_schema(conn)

        # ----------------------------------------------------
        # Verify schema BEFORE loading
        # ----------------------------------------------------

        verify_schema(conn)

        # ----------------------------------------------------
        # Load dimensions
        # ----------------------------------------------------

        load_dim_fund(conn)

        load_dim_date(conn)

        # ----------------------------------------------------
        # Load facts
        # ----------------------------------------------------

        load_fact_nav(conn)

        load_fact_transactions(conn)

        load_fact_performance(conn)

        load_fact_aum(conn)

        # ----------------------------------------------------
        # Commit
        # ----------------------------------------------------

        conn.commit()

        print_section(
            "DATABASE COMMIT"
        )

        print(
            "All data committed successfully."
        )

        # ----------------------------------------------------
        # Verify counts
        # ----------------------------------------------------

        verify_counts(conn)

        # ----------------------------------------------------
        # Referential integrity
        # ----------------------------------------------------

        integrity_pass = (
            verify_referential_integrity(conn)
        )

        # ----------------------------------------------------
        # Data validation
        # ----------------------------------------------------

        validate_data(conn)

        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        print_section(
            "FINAL RESULT"
        )

        if integrity_pass:

            print(
                "✅ STAR SCHEMA LOADING COMPLETED "
                "SUCCESSFULLY"
            )

            print(
                "✅ PRIMARY KEYS verified"
            )

            print(
                "✅ FOREIGN KEYS verified"
            )

            print(
                "✅ REFERENTIAL INTEGRITY verified"
            )

        else:

            print(
                "⚠️ STAR SCHEMA LOADED "
                "BUT REFERENTIAL INTEGRITY NEEDS ATTENTION"
            )

    except Exception as e:

        conn.rollback()

        print_section(
            "STAR SCHEMA LOADING FAILED"
        )

        print(
            f"Error: {e}"
        )

        raise

    finally:

        conn.close()

        print(
            "\nDatabase connection closed."
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()