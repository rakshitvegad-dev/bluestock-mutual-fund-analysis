import sqlite3
import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "bluestock_mf.db"

REPORTS_DIR = BASE_DIR / "reports"

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# SQL ANALYSIS QUERIES
# ============================================================

QUERIES = {

    # --------------------------------------------------------
    # QUERY 1
    # --------------------------------------------------------

    "01_top_fund_houses_by_aum": """

        SELECT
            fund_house,
            ROUND(SUM(aum_crore), 2) AS total_aum_crore

        FROM fact_aum

        GROUP BY fund_house

        ORDER BY total_aum_crore DESC

        LIMIT 5;

    """,

    # --------------------------------------------------------
    # QUERY 2
    # --------------------------------------------------------

    "02_average_nav_by_month": """

        SELECT
            d.year,
            d.month,
            d.month_name,
            ROUND(AVG(n.nav), 4) AS average_nav

        FROM fact_nav n

        JOIN dim_date d
            ON n.date_key = d.date_key

        GROUP BY
            d.year,
            d.month,
            d.month_name

        ORDER BY
            d.year,
            d.month;

    """,

    # --------------------------------------------------------
    # QUERY 3
    # --------------------------------------------------------

    "03_sip_inflow_yoy_growth": """

        WITH yearly_sip AS (

            SELECT
                strftime('%Y', month) AS year,
                SUM(sip_inflow_crore) AS total_sip_inflow_crore

            FROM monthly_sip_inflow

            GROUP BY
                strftime('%Y', month)
        )

        SELECT
            year,

            ROUND(
                total_sip_inflow_crore,
                2
            ) AS total_sip_inflow_crore,

            ROUND(
                LAG(total_sip_inflow_crore)
                OVER (
                    ORDER BY year
                ),
                2
            ) AS previous_year_inflow,

            ROUND(
                (
                    total_sip_inflow_crore
                    -
                    LAG(total_sip_inflow_crore)
                    OVER (
                        ORDER BY year
                    )
                )
                /
                NULLIF(
                    LAG(total_sip_inflow_crore)
                    OVER (
                        ORDER BY year
                    ),
                    0
                )
                * 100,
                2
            ) AS yoy_growth_pct

        FROM yearly_sip

        ORDER BY year;

    """,

    # --------------------------------------------------------
    # QUERY 4
    # --------------------------------------------------------

    "04_transactions_by_state": """

        SELECT
            state,
            COUNT(*) AS transaction_count,
            ROUND(
                SUM(amount_inr),
                2
            ) AS total_transaction_amount

        FROM fact_transactions

        WHERE state IS NOT NULL

        GROUP BY state

        ORDER BY total_transaction_amount DESC;

    """,

    # --------------------------------------------------------
    # QUERY 5
    # --------------------------------------------------------

    "05_low_expense_ratio_funds": """

        SELECT
            d.amfi_code,
            d.scheme_name,
            d.fund_house,
            d.category,
            d.sub_category,
            ROUND(
                d.expense_ratio_pct,
                2
            ) AS expense_ratio_pct

        FROM dim_fund d

        WHERE d.expense_ratio_pct < 1.0

        ORDER BY
            d.expense_ratio_pct ASC;

    """,

    # --------------------------------------------------------
    # QUERY 6
    # --------------------------------------------------------

    "06_top_funds_by_3yr_return": """

        SELECT
            d.amfi_code,
            d.scheme_name,
            d.fund_house,

            ROUND(
                p.return_3yr_pct,
                2
            ) AS return_3yr_pct

        FROM fact_performance p

        JOIN dim_fund d
            ON p.amfi_code = d.amfi_code

        ORDER BY
            p.return_3yr_pct DESC

        LIMIT 5;

    """,

    # --------------------------------------------------------
    # QUERY 7
    # --------------------------------------------------------

    "07_top_funds_by_sharpe_ratio": """

        SELECT
            d.amfi_code,
            d.scheme_name,
            d.fund_house,

            ROUND(
                p.sharpe_ratio,
                2
            ) AS sharpe_ratio,

            p.risk_grade

        FROM fact_performance p

        JOIN dim_fund d
            ON p.amfi_code = d.amfi_code

        ORDER BY
            p.sharpe_ratio DESC

        LIMIT 5;

    """,

    # --------------------------------------------------------
    # QUERY 8
    # --------------------------------------------------------

    "08_lowest_max_drawdown": """

        SELECT
            d.amfi_code,
            d.scheme_name,
            d.fund_house,

            ROUND(
                p.max_drawdown_pct,
                2
            ) AS max_drawdown_pct

        FROM fact_performance p

        JOIN dim_fund d
            ON p.amfi_code = d.amfi_code

        ORDER BY
            p.max_drawdown_pct ASC

        LIMIT 5;

    """,

    # --------------------------------------------------------
    # QUERY 9
    # --------------------------------------------------------

    "09_transaction_summary_by_type": """

        SELECT
            transaction_type,

            COUNT(*) AS transaction_count,

            ROUND(
                AVG(amount_inr),
                2
            ) AS average_transaction_amount,

            ROUND(
                SUM(amount_inr),
                2
            ) AS total_transaction_amount

        FROM fact_transactions

        GROUP BY
            transaction_type

        ORDER BY
            total_transaction_amount DESC;

    """,

    # --------------------------------------------------------
    # QUERY 10
    # --------------------------------------------------------

    "10_fund_house_performance": """

        SELECT
            d.fund_house,

            COUNT(*) AS number_of_funds,

            ROUND(
                AVG(p.return_3yr_pct),
                2
            ) AS avg_3yr_return,

            ROUND(
                AVG(p.sharpe_ratio),
                2
            ) AS avg_sharpe_ratio,

            ROUND(
                AVG(p.expense_ratio_pct),
                2
            ) AS avg_expense_ratio

        FROM fact_performance p

        JOIN dim_fund d
            ON p.amfi_code = d.amfi_code

        GROUP BY
            d.fund_house

        ORDER BY
            avg_3yr_return DESC;

    """
}


# ============================================================
# RUN ANALYSIS
# ============================================================

def main():

    print()
    print("=" * 70)
    print("MUTUAL FUND SQL ANALYSIS")
    print("=" * 70)

    print()
    print(f"Database : {DB_PATH}")
    print(f"Reports  : {REPORTS_DIR}")

    conn = get_connection()

    results = {}

    try:

        # ----------------------------------------------------
        # Verify database tables
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("DATABASE TABLE CHECK")
        print("=" * 70)

        tables = [
            row[0]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()
        ]

        for table in tables:

            print(
                f"{table:35} PASS"
            )

        # ----------------------------------------------------
        # Run queries
        # ----------------------------------------------------

        for number, (name, query) in enumerate(
            QUERIES.items(),
            start=1
        ):

            print()
            print("=" * 70)
            print(
                f"QUERY {number}: "
                f"{name.upper()}"
            )
            print("=" * 70)

            try:

                df = pd.read_sql_query(
                    query,
                    conn
                )

                results[name] = df

                print()
                print(
                    f"Rows returned: {len(df):,}"
                )

                if df.empty:

                    print(
                        "WARNING: Query returned no rows."
                    )

                else:

                    print(
                        df.to_string(
                            index=False
                        )
                    )

                # ------------------------------------------------
                # Save individual CSV
                # ------------------------------------------------

                output_file = (
                    REPORTS_DIR /
                    f"{name}.csv"
                )

                df.to_csv(
                    output_file,
                    index=False
                )

                print()
                print(
                    f"Saved: {output_file}"
                )

            except Exception as error:

                print()
                print(
                    f"QUERY FAILED: {error}"
                )

        # ----------------------------------------------------
        # Export Excel workbook
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("CREATING EXCEL REPORT")
        print("=" * 70)

        excel_file = (
            REPORTS_DIR /
            "SQL_Analysis_Results.xlsx"
        )

        with pd.ExcelWriter(
            excel_file,
            engine="openpyxl"
        ) as writer:

            for sheet_name, df in results.items():

                # Excel sheet names max = 31 chars
                safe_sheet_name = (
                    sheet_name[:31]
                )

                df.to_excel(
                    writer,
                    sheet_name=safe_sheet_name,
                    index=False
                )

        print(
            f"Excel report saved:\n{excel_file}"
        )

        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("SQL ANALYSIS COMPLETED")
        print("=" * 70)

        print()
        print(
            f"Queries executed : {len(results)}"
        )

        print(
            f"CSV reports      : {len(results)}"
        )

        print(
            f"Excel report     : SQL_Analysis_Results.xlsx"
        )

        print()
        print(
            "NEXT STEP: EDA INSIGHTS + DASHBOARD"
        )

    finally:

        conn.close()

        print()
        print(
            "Database connection closed."
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()