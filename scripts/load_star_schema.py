"""
Bluestock Mutual Fund Analytics
Star Schema Loader

Purpose:
    Build and populate the SQLite star schema.

Dimensions:
    dim_fund
    dim_date

Facts:
    fact_nav
    fact_transactions
    fact_performance
    fact_aum

Core NAV dataset:
    data/processed/nav_history_cleaned.csv

Important:
    The 40-fund historical nav_history dataset is the core
    analytical dataset. Live *_Direct.csv files are NOT used
    to replace nav_history.csv.
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys


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
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def check_file(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found:\n{path}"
        )


def safe_value(value):
    """
    Convert pandas values into SQLite-safe Python values.
    """
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")

    return value


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    print_section("CREATING SQLITE DATABASE")

    # --------------------------------------------------------
    # Remove old database
    # --------------------------------------------------------

    if DB_PATH.exists():

        DB_PATH.unlink()

        print(
            f"Old database removed: {DB_PATH}"
        )

    # --------------------------------------------------------
    # Create new database
    # --------------------------------------------------------

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    print(
        f"New database created: {DB_PATH}"
    )

    print(
        "Foreign keys: ENABLED"
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
        f"Schema file size: "
        f"{len(schema_sql):,} characters"
    )

    print(
        "PRIMARY KEY found in schema:",
        "PRIMARY KEY" in schema_sql.upper()
    )

    print(
        "FOREIGN KEY found in schema:",
        "FOREIGN KEY" in schema_sql.upper()
    )

    conn.executescript(schema_sql)

    print(
        "Schema SQL executed successfully."
    )


# ============================================================
# SQLITE SCHEMA HELPERS
# ============================================================

def get_tables(conn):

    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        """
    ).fetchall()

    return {
        row[0]
        for row in rows
    }


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

    return conn.execute(
        f"PRAGMA foreign_key_list([{table}])"
    ).fetchall()


# ============================================================
# VERIFY SCHEMA
# ============================================================

def verify_schema(conn):

    print_section(
        "VERIFYING ACTUAL SQLITE SCHEMA"
    )

    expected_tables = [
        "dim_fund",
        "dim_date",
        "fact_nav",
        "fact_transactions",
        "fact_performance",
        "fact_aum"
    ]

    actual_tables = get_tables(conn)

    # --------------------------------------------------------
    # TABLE CHECK
    # --------------------------------------------------------

    print()
    print("TABLE CHECK")
    print("-" * 70)

    all_tables_exist = True

    for table in expected_tables:

        exists = table in actual_tables

        status = (
            "PASS"
            if exists
            else "FAIL"
        )

        print(
            f"{table:30} {status}"
        )

        if not exists:
            all_tables_exist = False

    if not all_tables_exist:

        raise ValueError(
            "One or more required star-schema tables "
            "are missing."
        )

    # --------------------------------------------------------
    # PRIMARY KEY CHECK
    # --------------------------------------------------------

    print()
    print("PRIMARY KEY CHECK")
    print("-" * 70)

    for table in expected_tables:

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
            f"{table:30} "
            f"{status} -> {primary_keys}"
        )

        if not primary_keys:

            raise ValueError(
                f"Table {table} has no primary key."
            )

    # --------------------------------------------------------
    # FOREIGN KEY CHECK
    # --------------------------------------------------------

    print()
    print("FOREIGN KEY CHECK")
    print("-" * 70)

    for table in expected_tables:

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

                print(
                    f"    {fk[3]} -> "
                    f"{fk[2]}.{fk[4]}"
                )

        else:

            print(
                f"{table:30} PASS -> "
                f"0 foreign key(s)"
            )

    print()
    print(
        "SQLite schema verification completed."
    )


# ============================================================
# LOAD DIM_FUND
# ============================================================

def load_dim_fund(conn):

    print()
    print("Loading dim_fund...")

    path = RAW_DIR / "fund_master.csv"

    check_file(path)

    df = pd.read_csv(path)

    print(
        f"Source rows: {len(df):,}"
    )

    required_columns = [
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
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in fund_master.csv:\n"
            + str(missing_columns)
        )

    df = df[
        required_columns
    ].copy()

    # --------------------------------------------------------
    # AMFI code validation
    # --------------------------------------------------------

    df["amfi_code"] = pd.to_numeric(
        df["amfi_code"],
        errors="coerce"
    )

    if df["amfi_code"].isna().any():

        raise ValueError(
            "fund_master.csv contains invalid AMFI codes."
        )

    df["amfi_code"] = (
        df["amfi_code"]
        .astype(int)
    )

    duplicate_codes = (
        df["amfi_code"]
        .duplicated()
        .sum()
    )

    if duplicate_codes > 0:

        raise ValueError(
            f"Duplicate AMFI codes found: "
            f"{duplicate_codes}"
        )

    # --------------------------------------------------------
    # Date conversion
    # --------------------------------------------------------

    df["launch_date"] = pd.to_datetime(
        df["launch_date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    # --------------------------------------------------------
    # Insert
    # --------------------------------------------------------

    insert_sql = """
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
    """

    for _, row in df.iterrows():

        values = tuple(
            safe_value(value)
            for value in row
        )

        conn.execute(
            insert_sql,
            values
        )

    print(
        f"dim_fund loaded: {len(df):,}"
    )


# ============================================================
# COLLECT ALL DATES
# ============================================================

def collect_all_dates():

    print()
    print("Collecting dates for dim_date...")

    all_dates = set()

    # --------------------------------------------------------
    # NAV dates
    # --------------------------------------------------------

    nav_path = (
        PROCESSED_DIR
        / "nav_history_cleaned.csv"
    )

    check_file(nav_path)

    nav = pd.read_csv(nav_path)

    if "date" not in nav.columns:

        raise ValueError(
            "date column missing from "
            "nav_history_cleaned.csv"
        )

    nav_dates = pd.to_datetime(
        nav["date"],
        errors="coerce"
    ).dropna()

    nav_date_strings = (
        nav_dates
        .dt.strftime("%Y-%m-%d")
        .tolist()
    )

    all_dates.update(
        nav_date_strings
    )

    print(
        f"NAV dates collected: "
        f"{len(nav_date_strings):,}"
    )

    # --------------------------------------------------------
    # Transaction dates
    # --------------------------------------------------------

    transaction_path = (
        PROCESSED_DIR
        / "investor_transactions_cleaned.csv"
    )

    check_file(transaction_path)

    transactions = pd.read_csv(
        transaction_path
    )

    if "transaction_date" not in transactions.columns:

        raise ValueError(
            "transaction_date column missing from "
            "investor_transactions_cleaned.csv"
        )

    transaction_dates = pd.to_datetime(
        transactions["transaction_date"],
        errors="coerce"
    ).dropna()

    transaction_date_strings = (
        transaction_dates
        .dt.strftime("%Y-%m-%d")
        .tolist()
    )

    all_dates.update(
        transaction_date_strings
    )

    print(
        f"Transaction dates collected: "
        f"{len(transaction_date_strings):,}"
    )

    # --------------------------------------------------------
    # AUM dates
    # --------------------------------------------------------

    aum_path = (
        RAW_DIR
        / "aum_by_fund_house.csv"
    )

    check_file(aum_path)

    aum = pd.read_csv(aum_path)

    if "date" not in aum.columns:

        raise ValueError(
            "date column missing from "
            "aum_by_fund_house.csv"
        )

    aum_dates = pd.to_datetime(
        aum["date"],
        errors="coerce"
    ).dropna()

    aum_date_strings = (
        aum_dates
        .dt.strftime("%Y-%m-%d")
        .tolist()
    )

    all_dates.update(
        aum_date_strings
    )

    print(
        f"AUM dates collected: "
        f"{len(aum_date_strings):,}"
    )

    # --------------------------------------------------------
    # Final check
    # --------------------------------------------------------

    if not all_dates:

        raise ValueError(
            "No valid dates found for dim_date."
        )

    print(
        f"Unique dates collected: "
        f"{len(all_dates):,}"
    )

    return sorted(all_dates)


# ============================================================
# LOAD DIM_DATE
# ============================================================

def load_dim_date(conn):

    print()
    print("Loading dim_date...")

    date_strings = collect_all_dates()

    dates = pd.DataFrame(
        {
            "full_date": pd.to_datetime(
                date_strings
            )
        }
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
    # Insert
    # --------------------------------------------------------

    insert_sql = """
        INSERT INTO dim_date (
            date_key,
            full_date,
            year,
            month,
            month_name,
            quarter
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """

    for _, row in dates.iterrows():

        conn.execute(
            insert_sql,
            (
                int(row["date_key"]),

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
        f"dim_date loaded: "
        f"{len(dates):,}"
    )


# ============================================================
# LOAD FACT_NAV
# ============================================================

def load_fact_nav(conn):

    print()
    print("Loading fact_nav...")

    path = (
        PROCESSED_DIR
        / "nav_history_cleaned.csv"
    )

    check_file(path)

    nav = pd.read_csv(path)

    required_columns = [
        "amfi_code",
        "date",
        "nav"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in nav.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in "
            "nav_history_cleaned.csv:\n"
            + str(missing_columns)
        )

    print(
        f"Source NAV rows: "
        f"{len(nav):,}"
    )

    # --------------------------------------------------------
    # Convert types
    # --------------------------------------------------------

    nav["amfi_code"] = pd.to_numeric(
        nav["amfi_code"],
        errors="coerce"
    )

    nav["date"] = pd.to_datetime(
        nav["date"],
        errors="coerce"
    )

    nav["nav"] = pd.to_numeric(
        nav["nav"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if nav["amfi_code"].isna().any():

        raise ValueError(
            "fact_nav contains invalid AMFI codes."
        )

    if nav["date"].isna().any():

        raise ValueError(
            "fact_nav contains invalid dates."
        )

    if nav["nav"].isna().any():

        raise ValueError(
            "fact_nav contains NULL NAV values."
        )

    if (nav["nav"] <= 0).any():

        raise ValueError(
            "fact_nav contains NAV values <= 0."
        )

    nav["amfi_code"] = (
        nav["amfi_code"]
        .astype(int)
    )

    # --------------------------------------------------------
    # Create date key
    # --------------------------------------------------------

    nav["date_key"] = (
        nav["date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    # --------------------------------------------------------
    # Validate duplicate fund/date
    # --------------------------------------------------------

    duplicates = nav.duplicated(
        subset=[
            "amfi_code",
            "date_key"
        ]
    ).sum()

    if duplicates > 0:

        raise ValueError(
            "Duplicate AMFI/date records found "
            f"in fact_nav: {duplicates}"
        )

    # --------------------------------------------------------
    # Validate fund references
    # --------------------------------------------------------

    dim_funds = {
        row[0]
        for row in conn.execute(
            """
            SELECT amfi_code
            FROM dim_fund
            """
        ).fetchall()
    }

    missing_funds = sorted(
        set(nav["amfi_code"])
        - dim_funds
    )

    if missing_funds:

        raise ValueError(
            "NAV contains AMFI codes not found "
            f"in dim_fund:\n{missing_funds}"
        )

    # --------------------------------------------------------
    # Validate date references
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

    missing_dates = sorted(
        set(nav["date_key"])
        - dim_dates
    )

    if missing_dates:

        raise ValueError(
            "NAV contains date_key values not found "
            f"in dim_date:\n{missing_dates[:20]}"
        )

    # --------------------------------------------------------
    # Insert
    # --------------------------------------------------------

    insert_sql = """
        INSERT INTO fact_nav (
            amfi_code,
            date_key,
            nav
        )
        VALUES (?, ?, ?)
    """

    for _, row in nav.iterrows():

        conn.execute(
            insert_sql,
            (
                int(row["amfi_code"]),

                int(row["date_key"]),

                float(row["nav"])
            )
        )

    print(
        f"fact_nav loaded: "
        f"{len(nav):,}"
    )

    print(
        f"Unique funds: "
        f"{nav['amfi_code'].nunique():,}"
    )


# ============================================================
# LOAD FACT_TRANSACTIONS
# ============================================================

def load_fact_transactions(conn):

    print()
    print("Loading fact_transactions...")

    path = (
        PROCESSED_DIR
        / "investor_transactions_cleaned.csv"
    )

    check_file(path)

    df = pd.read_csv(path)

    required_columns = [
        "investor_id",
        "transaction_date",
        "amfi_code",
        "transaction_type",
        "amount_inr",
        "state",
        "city",
        "city_tier",
        "age_group",
        "gender",
        "annual_income_lakh",
        "payment_mode",
        "kyc_status"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in "
            "investor_transactions_cleaned.csv:\n"
            + str(missing_columns)
        )

    df = df[
        required_columns
    ].copy()

    print(
        f"Source transaction rows: "
        f"{len(df):,}"
    )

    # --------------------------------------------------------
    # Convert dates
    # --------------------------------------------------------

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce"
    )

    if df["transaction_date"].isna().any():

        raise ValueError(
            "Invalid transaction dates found."
        )

    df["transaction_date"] = (
        df["transaction_date"]
        .dt.strftime("%Y-%m-%d")
    )

    # --------------------------------------------------------
    # Convert numeric fields
    # --------------------------------------------------------

    df["amount_inr"] = pd.to_numeric(
        df["amount_inr"],
        errors="coerce"
    )

    if df["amount_inr"].isna().any():

        raise ValueError(
            "NULL/invalid amount_inr values found."
        )

    if (df["amount_inr"] <= 0).any():

        raise ValueError(
            "Transaction amount must be > 0."
        )

    df["amfi_code"] = pd.to_numeric(
        df["amfi_code"],
        errors="coerce"
    )

    if df["amfi_code"].isna().any():

        raise ValueError(
            "Invalid AMFI codes found in transactions."
        )

    df["amfi_code"] = (
        df["amfi_code"]
        .astype(int)
    )

    # --------------------------------------------------------
    # Validate fund references
    # --------------------------------------------------------

    dim_funds = {
        row[0]
        for row in conn.execute(
            """
            SELECT amfi_code
            FROM dim_fund
            """
        ).fetchall()
    }

    missing_funds = sorted(
        set(df["amfi_code"])
        - dim_funds
    )

    if missing_funds:

        raise ValueError(
            "Transactions contain AMFI codes not found "
            f"in dim_fund:\n{missing_funds}"
        )

    # --------------------------------------------------------
    # Insert
    # --------------------------------------------------------

    insert_sql = """
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
    """

    for _, row in df.iterrows():

        values = tuple(
            safe_value(value)
            for value in row
        )

        conn.execute(
            insert_sql,
            values
        )

    print(
        f"fact_transactions loaded: "
        f"{len(df):,}"
    )


# ============================================================
# LOAD FACT_PERFORMANCE
# ============================================================

def load_fact_performance(conn):

    print()
    print("Loading fact_performance...")

    path = (
        PROCESSED_DIR
        / "cleaned_scheme_performance.csv"
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
        column
        for column in columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in "
            "cleaned_scheme_performance.csv:\n"
            + str(missing_columns)
        )

    df = df[
        columns
    ].copy()

    print(
        f"Source performance rows: "
        f"{len(df):,}"
    )

    # --------------------------------------------------------
    # AMFI validation
    # --------------------------------------------------------

    df["amfi_code"] = pd.to_numeric(
        df["amfi_code"],
        errors="coerce"
    )

    if df["amfi_code"].isna().any():

        raise ValueError(
            "Invalid AMFI codes in performance data."
        )

    df["amfi_code"] = (
        df["amfi_code"]
        .astype(int)
    )

    dim_funds = {
        row[0]
        for row in conn.execute(
            """
            SELECT amfi_code
            FROM dim_fund
            """
        ).fetchall()
    }

    missing_funds = sorted(
        set(df["amfi_code"])
        - dim_funds
    )

    if missing_funds:

        raise ValueError(
            "Performance data contains AMFI codes "
            "not found in dim_fund:\n"
            + str(missing_funds)
        )

    # --------------------------------------------------------
    # Insert
    # --------------------------------------------------------

    insert_sql = """
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
    """

    for _, row in df.iterrows():

        values = tuple(
            safe_value(value)
            for value in row
        )

        conn.execute(
            insert_sql,
            values
        )

    print(
        f"fact_performance loaded: "
        f"{len(df):,}"
    )


# ============================================================
# LOAD FACT_AUM
# ============================================================

def load_fact_aum(conn):

    print()
    print("Loading fact_aum...")

    path = (
        RAW_DIR
        / "aum_by_fund_house.csv"
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
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in "
            "aum_by_fund_house.csv:\n"
            + str(missing_columns)
        )

    df = df[
        required_columns
    ].copy()

    print(
        f"Source AUM rows: "
        f"{len(df):,}"
    )

    # --------------------------------------------------------
    # Date conversion
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    if df["date"].isna().any():

        raise ValueError(
            "Invalid AUM dates found."
        )

    df["date_key"] = (
        df["date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    df["aum_lakh_crore"] = pd.to_numeric(
        df["aum_lakh_crore"],
        errors="coerce"
    )

    df["aum_crore"] = pd.to_numeric(
        df["aum_crore"],
        errors="coerce"
    )

    df["num_schemes"] = pd.to_numeric(
        df["num_schemes"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Check date references
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
        set(df["date_key"])
        - dim_dates
    )

    if missing_date_keys:

        raise ValueError(
            "AUM contains date_key values not found "
            "in dim_date:\n"
            + str(missing_date_keys[:20])
        )

    # --------------------------------------------------------
    # Insert
    # --------------------------------------------------------

    insert_sql = """
        INSERT INTO fact_aum (
            date_key,
            fund_house,
            aum_lakh_crore,
            aum_crore,
            num_schemes
        )
        VALUES (?, ?, ?, ?, ?)
    """

    for _, row in df.iterrows():

        conn.execute(
            insert_sql,
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
        f"fact_aum loaded: "
        f"{len(df):,}"
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
    # FUND COUNT
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
        f"Unique funds in dim_fund : "
        f"{fund_count}"
    )

    print(
        f"Unique funds in fact_nav : "
        f"{nav_fund_count}"
    )

    if fund_count == nav_fund_count:

        print(
            "AMFI fund count validation: PASS"
        )

    else:

        print(
            "AMFI fund count validation: FAIL"
        )

    # --------------------------------------------------------
    # NAV
    # --------------------------------------------------------

    invalid_nav = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_nav
        WHERE nav IS NULL
           OR nav <= 0
        """
    ).fetchone()[0]

    print(
        "\nNAV > 0 validation: "
        f"{'PASS' if invalid_nav == 0 else 'FAIL'} "
        f"Invalid rows={invalid_nav}"
    )

    # --------------------------------------------------------
    # TRANSACTIONS
    # --------------------------------------------------------

    invalid_transactions = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_transactions
        WHERE amount_inr IS NULL
           OR amount_inr <= 0
        """
    ).fetchone()[0]

    print(
        "Transaction amount > 0: "
        f"{'PASS' if invalid_transactions == 0 else 'FAIL'} "
        f"Invalid rows={invalid_transactions}"
    )

    # --------------------------------------------------------
    # PERFORMANCE
    # --------------------------------------------------------

    performance_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_performance
        """
    ).fetchone()[0]

    print(
        f"Performance records: "
        f"{performance_count:,}"
    )

    # --------------------------------------------------------
    # AUM
    # --------------------------------------------------------

    aum_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_aum
        """
    ).fetchone()[0]

    print(
        f"AUM records: "
        f"{aum_count:,}"
    )

    # --------------------------------------------------------
    # NULL CHECKS
    # --------------------------------------------------------

    null_nav = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_nav
        WHERE nav IS NULL
        """
    ).fetchone()[0]

    null_transaction_dates = conn.execute(
        """
        SELECT COUNT(*)
        FROM fact_transactions
        WHERE transaction_date IS NULL
        """
    ).fetchone()[0]

    print(
        "\nNULL NAV values: "
        f"{null_nav}"
    )

    print(
        "NULL transaction dates: "
        f"{null_transaction_dates}"
    )


# ============================================================
# VERIFY FOREIGN KEY ENFORCEMENT
# ============================================================

def verify_foreign_key_enforcement(conn):

    print_section(
        "FOREIGN KEY ENFORCEMENT"
    )

    result = conn.execute(
        "PRAGMA foreign_keys"
    ).fetchone()[0]

    if result == 1:

        print(
            "Foreign key enforcement: PASS"
        )

        return True

    print(
        "Foreign key enforcement: FAIL"
    )

    return False


# ============================================================
# MAIN
# ============================================================

def main():

    conn = None

    try:

        # ----------------------------------------------------
        # CREATE DATABASE
        # ----------------------------------------------------

        conn = create_database()

        # ----------------------------------------------------
        # CREATE SCHEMA
        # ----------------------------------------------------

        create_schema(conn)

        # ----------------------------------------------------
        # VERIFY SCHEMA
        # ----------------------------------------------------

        verify_schema(conn)

        verify_foreign_key_enforcement(conn)

        # ----------------------------------------------------
        # LOAD DIMENSIONS
        # ----------------------------------------------------

        print_section(
            "LOADING DIMENSION TABLES"
        )

        load_dim_fund(conn)

        load_dim_date(conn)

        # ----------------------------------------------------
        # LOAD FACT TABLES
        # ----------------------------------------------------

        print_section(
            "LOADING FACT TABLES"
        )

        load_fact_nav(conn)

        load_fact_transactions(conn)

        load_fact_performance(conn)

        load_fact_aum(conn)

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        conn.commit()

        print_section(
            "DATABASE COMMIT"
        )

        print(
            "All data committed successfully."
        )

        # ----------------------------------------------------
        # ROW COUNTS
        # ----------------------------------------------------

        verify_counts(conn)

        # ----------------------------------------------------
        # REFERENTIAL INTEGRITY
        # ----------------------------------------------------

        integrity_pass = (
            verify_referential_integrity(conn)
        )

        # ----------------------------------------------------
        # DATA VALIDATION
        # ----------------------------------------------------

        validate_data(conn)

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        print_section(
            "FINAL RESULT"
        )

        if integrity_pass:

            print(
                "STAR SCHEMA LOADING COMPLETED "
                "SUCCESSFULLY"
            )

            print(
                "PRIMARY KEYS verified"
            )

            print(
                "FOREIGN KEYS verified"
            )

            print(
                "REFERENTIAL INTEGRITY verified"
            )

            print(
                "DATA VALIDATION completed"
            )

            print()
            print(
                f"SQLite database:"
            )

            print(
                f"{DB_PATH}"
            )

            return 0

        else:

            print(
                "STAR SCHEMA LOADED BUT "
                "REFERENTIAL INTEGRITY NEEDS ATTENTION"
            )

            return 1

    except Exception as error:

        if conn is not None:

            conn.rollback()

        print()
        print("=" * 70)
        print("STAR SCHEMA LOADING FAILED")
        print("=" * 70)
        print(
            f"Error: {error}"
        )
        print("=" * 70)

        return 1

    finally:

        if conn is not None:

            conn.close()

            print()
            print(
                "Database connection closed."
            )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )