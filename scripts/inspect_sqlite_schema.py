import sqlite3
from pathlib import Path


# ------------------------------------------------------------
# Project / database path
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "bluestock_mf.db"


print("=" * 80)
print("SQLITE SCHEMA INSPECTION")
print("=" * 80)

print(f"Database: {DB_PATH}")

# ------------------------------------------------------------
# Check database exists
# ------------------------------------------------------------

if not DB_PATH.exists():
    print("\n❌ Database file not found.")
    raise SystemExit(1)


# ------------------------------------------------------------
# Connect
# ------------------------------------------------------------

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# ------------------------------------------------------------
# Get tables
# ------------------------------------------------------------

tables = cursor.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
    """
).fetchall()


print("\nTables found:")
print("-" * 80)

for table in tables:
    print(table[0])


# ------------------------------------------------------------
# Inspect each required table
# ------------------------------------------------------------

required_tables = [
    "dim_fund",
    "dim_date",
    "fact_nav",
    "fact_transactions",
    "fact_performance",
    "fact_aum",
]


for table in required_tables:

    print("\n" + "=" * 80)
    print(f"TABLE: {table}")
    print("=" * 80)

    result = cursor.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table,)
    ).fetchone()

    if result is None:
        print("❌ TABLE NOT FOUND")
        continue

    print(result[0])


# ------------------------------------------------------------
# Primary key check
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("PRIMARY KEY CHECK")
print("=" * 80)

for table in required_tables:

    columns = cursor.execute(
        f"PRAGMA table_info([{table}])"
    ).fetchall()

    primary_keys = [
        row[1]
        for row in columns
        if row[5] != 0
    ]

    print(
        f"{table:30} -> {primary_keys}"
    )


# ------------------------------------------------------------
# Foreign key check
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("FOREIGN KEY CHECK")
print("=" * 80)

for table in required_tables:

    foreign_keys = cursor.execute(
        f"PRAGMA foreign_key_list([{table}])"
    ).fetchall()

    print(f"\n{table}:")

    if not foreign_keys:
        print("  No foreign keys")

    else:

        for fk in foreign_keys:

            print(
                f"  {fk[3]} -> "
                f"{fk[2]}.{fk[4]}"
            )


# ------------------------------------------------------------
# Close
# ------------------------------------------------------------

conn.close()

print("\n" + "=" * 80)
print("INSPECTION COMPLETED")
print("=" * 80)