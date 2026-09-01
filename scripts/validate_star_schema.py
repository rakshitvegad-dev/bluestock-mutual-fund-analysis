import sqlite3
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "bluestock_mf.db"


# ============================================================
# Database Connection
# ============================================================

def connect_database():
    conn = sqlite3.connect(DB_PATH)

    # Enable foreign-key enforcement
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ============================================================
# Get Tables
# ============================================================

def get_tables(cursor):

    return cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()


# ============================================================
# Validate Required Tables
# ============================================================

def validate_tables(cursor):

    expected_tables = {
        "dim_fund",
        "dim_date",
        "fact_nav",
        "fact_transactions",
        "fact_performance",
        "fact_aum",
    }

    actual_tables = {
        row[0]
        for row in get_tables(cursor)
    }

    print("\nTABLE VALIDATION")
    print("=" * 70)

    all_pass = True

    for table in sorted(expected_tables):

        if table in actual_tables:
            print(f"{table:30} PASS")
        else:
            print(f"{table:30} FAIL")
            all_pass = False

    return all_pass


# ============================================================
# Validate Row Counts
# ============================================================

def validate_row_counts(cursor):

    tables = [
        "dim_fund",
        "dim_date",
        "fact_nav",
        "fact_transactions",
        "fact_performance",
        "fact_aum",
    ]

    print("\nROW COUNTS")
    print("=" * 70)

    expected_counts = {
        "dim_fund": 40,
        "fact_nav": 46000,
        "fact_transactions": 32778,
        "fact_performance": 40,
        "fact_aum": 90,
    }

    all_pass = True

    for table in tables:

        count = cursor.execute(
            f"SELECT COUNT(*) FROM [{table}]"
        ).fetchone()[0]

        if table in expected_counts:

            expected = expected_counts[table]

            status = "PASS" if count == expected else "CHECK"

            if count != expected:
                all_pass = False

            print(
                f"{table:30} "
                f"{count:10,} "
                f"(expected {expected:,}) "
                f"{status}"
            )

        else:

            print(
                f"{table:30} "
                f"{count:10,}"
            )

    return all_pass


# ============================================================
# Validate Required Columns
# ============================================================

def validate_columns(cursor):

    required_columns = {

        "dim_fund": [
            "amfi_code",
            "fund_house",
            "scheme_name",
            "category",
            "sub_category",
            "plan",
            "risk_category",
        ],

        "dim_date": [
            "date_key",
            "full_date",
            "year",
            "month",
            "month_name",
            "quarter",
        ],

        "fact_nav": [
            "amfi_code",
            "date_key",
            "nav",
        ],

        "fact_transactions": [
            "investor_id",
            "transaction_date",
            "amfi_code",
            "transaction_type",
            "amount_inr",
        ],

        "fact_performance": [
            "amfi_code",
            "return_1yr_pct",
            "return_3yr_pct",
            "return_5yr_pct",
            "sharpe_ratio",
            "sortino_ratio",
        ],

        "fact_aum": [
            "date_key",
            "fund_house",
            "aum_lakh_crore",
            "aum_crore",
            "num_schemes",
        ],
    }

    print("\nCOLUMN VALIDATION")
    print("=" * 70)

    all_pass = True

    for table, columns in required_columns.items():

        actual_columns = {
            row[1]
            for row in cursor.execute(
                f"PRAGMA table_info([{table}])"
            ).fetchall()
        }

        for column in columns:

            if column in actual_columns:

                print(
                    f"{table}.{column:25} PASS"
                )

            else:

                print(
                    f"{table}.{column:25} FAIL"
                )

                all_pass = False

    return all_pass


# ============================================================
# NULL Validation
# ============================================================

def validate_nulls(cursor):

    print("\nNULL CHECK")
    print("=" * 70)

    checks = {

        "dim_fund": [
            "amfi_code",
        ],

        "dim_date": [
            "date_key",
            "full_date",
        ],

        "fact_nav": [
            "amfi_code",
            "date_key",
            "nav",
        ],

        "fact_transactions": [
            "amfi_code",
            "transaction_date",
            "amount_inr",
        ],

        "fact_performance": [
            "amfi_code",
        ],

        "fact_aum": [
            "date_key",
            "fund_house",
        ],
    }

    all_pass = True

    for table, columns in checks.items():

        for column in columns:

            query = f"""
                SELECT COUNT(*)
                FROM [{table}]
                WHERE [{column}] IS NULL
            """

            count = cursor.execute(query).fetchone()[0]

            status = "PASS" if count == 0 else "FAIL"

            if count != 0:
                all_pass = False

            print(
                f"{table}.{column:20} "
                f"{status} "
                f"NULLs={count}"
            )

    return all_pass


# ============================================================
# Primary Key Validation
# ============================================================

def validate_primary_keys(cursor):

    print("\nPRIMARY KEY VALIDATION")
    print("=" * 70)

    tables = [
        "dim_fund",
        "dim_date",
        "fact_nav",
        "fact_transactions",
        "fact_performance",
        "fact_aum",
    ]

    all_pass = True

    for table in tables:

        columns = cursor.execute(
            f"PRAGMA table_info([{table}])"
        ).fetchall()

        primary_keys = [
            row[1]
            for row in columns
            if row[5] == 1
        ]

        if primary_keys:

            print(
                f"{table:30} "
                f"PASS "
                f"PK={primary_keys}"
            )

        else:

            print(
                f"{table:30} "
                f"FAIL - No primary key"
            )

            all_pass = False

    return all_pass


# ============================================================
# Foreign Key Validation
# ============================================================

def validate_foreign_keys(cursor):

    print("\nFOREIGN KEY VALIDATION")
    print("=" * 70)

    tables = [
        "fact_nav",
        "fact_transactions",
        "fact_performance",
        "fact_aum",
    ]

    all_pass = True

    for table in tables:

        foreign_keys = cursor.execute(
            f"PRAGMA foreign_key_list([{table}])"
        ).fetchall()

        if foreign_keys:

            print(f"\n{table}:")

            for fk in foreign_keys:

                print(
                    f"  {fk[3]} -> "
                    f"{fk[2]}.{fk[4]}"
                )

        else:

            print(
                f"{table:30} "
                f"FAIL - No foreign keys"
            )

            all_pass = False

    return all_pass


# ============================================================
# Duplicate AMFI Code Validation
# ============================================================

def validate_fund_codes(cursor):

    print("\nFUND CODE VALIDATION")
    print("=" * 70)

    total_codes = cursor.execute(
        """
        SELECT COUNT(DISTINCT amfi_code)
        FROM dim_fund
        """
    ).fetchone()[0]

    duplicate_codes = cursor.execute(
        """
        SELECT amfi_code, COUNT(*)
        FROM dim_fund
        GROUP BY amfi_code
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    print(
        f"Unique AMFI codes: {total_codes}"
    )

    if total_codes == 40 and not duplicate_codes:

        print(
            "AMFI code validation: PASS"
        )

        return True

    print(
        "AMFI code validation: FAIL"
    )

    return False


# ============================================================
# Referential Integrity Validation
# ============================================================

def validate_referential_integrity(cursor):

    print("\nREFERENTIAL INTEGRITY")
    print("=" * 70)

    checks = {

        "fact_nav": """
            SELECT COUNT(*)
            FROM fact_nav f
            LEFT JOIN dim_fund d
                ON f.amfi_code = d.amfi_code
            WHERE d.amfi_code IS NULL
        """,

        "fact_transactions": """
            SELECT COUNT(*)
            FROM fact_transactions f
            LEFT JOIN dim_fund d
                ON f.amfi_code = d.amfi_code
            WHERE d.amfi_code IS NULL
        """,

        "fact_performance": """
            SELECT COUNT(*)
            FROM fact_performance f
            LEFT JOIN dim_fund d
                ON f.amfi_code = d.amfi_code
            WHERE d.amfi_code IS NULL
        """,
    }

    all_pass = True

    for table, query in checks.items():

        orphan_rows = cursor.execute(query).fetchone()[0]

        status = "PASS" if orphan_rows == 0 else "FAIL"

        if orphan_rows != 0:
            all_pass = False

        print(
            f"{table:30} "
            f"{status} "
            f"Orphan rows={orphan_rows}"
        )

    return all_pass


# ============================================================
# NAV Validation
# ============================================================

def validate_nav(cursor):

    print("\nNAV VALIDATION")
    print("=" * 70)

    invalid_nav = cursor.execute(
        """
        SELECT COUNT(*)
        FROM fact_nav
        WHERE nav <= 0
        """
    ).fetchone()[0]

    status = "PASS" if invalid_nav == 0 else "FAIL"

    print(
        f"NAV > 0 validation: {status} "
        f"Invalid rows={invalid_nav}"
    )

    return invalid_nav == 0


# ============================================================
# Transaction Amount Validation
# ============================================================

def validate_transactions(cursor):

    print("\nTRANSACTION VALIDATION")
    print("=" * 70)

    invalid_amounts = cursor.execute(
        """
        SELECT COUNT(*)
        FROM fact_transactions
        WHERE amount_inr <= 0
        """
    ).fetchone()[0]

    status = (
        "PASS"
        if invalid_amounts == 0
        else "FAIL"
    )

    print(
        f"Transaction amount > 0: {status} "
        f"Invalid rows={invalid_amounts}"
    )

    return invalid_amounts == 0


# ============================================================
# Performance Validation
# ============================================================

def validate_performance(cursor):

    print("\nPERFORMANCE VALIDATION")
    print("=" * 70)

    performance_count = cursor.execute(
        """
        SELECT COUNT(*)
        FROM fact_performance
        """
    ).fetchone()[0]

    status = (
        "PASS"
        if performance_count == 40
        else "CHECK"
    )

    print(
        f"Performance records: "
        f"{performance_count} "
        f"(expected 40) "
        f"{status}"
    )

    return performance_count == 40


# ============================================================
# Main
# ============================================================

def main():

    if not DB_PATH.exists():

        print(
            f"ERROR: Database not found:\n{DB_PATH}"
        )

        return

    conn = connect_database()
    cursor = conn.cursor()

    print("=" * 70)
    print("MUTUAL FUND STAR SCHEMA VALIDATION")
    print("=" * 70)

    results = []

    results.append(
        validate_tables(cursor)
    )

    results.append(
        validate_row_counts(cursor)
    )

    results.append(
        validate_columns(cursor)
    )

    results.append(
        validate_nulls(cursor)
    )

    results.append(
        validate_primary_keys(cursor)
    )

    results.append(
        validate_foreign_keys(cursor)
    )

    results.append(
        validate_fund_codes(cursor)
    )

    results.append(
        validate_referential_integrity(cursor)
    )

    results.append(
        validate_nav(cursor)
    )

    results.append(
        validate_transactions(cursor)
    )

    results.append(
        validate_performance(cursor)
    )

    conn.close()

    print("\n" + "=" * 70)
    print("FINAL VALIDATION RESULT")
    print("=" * 70)

    if all(results):

        print("ALL STAR SCHEMA VALIDATIONS PASSED")

    else:

        print(
            "🟡 SOME VALIDATIONS NEED ATTENTION"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()