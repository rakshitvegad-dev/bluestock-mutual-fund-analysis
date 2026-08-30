import sqlite3

conn = sqlite3.connect(r"D:\mutual-fund-analysis\bluestock_mf.db")

tables = conn.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""").fetchall()

print("Tables in database:")

for table in tables:
    print(table[0])

conn.close()