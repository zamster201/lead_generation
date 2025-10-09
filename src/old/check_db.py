import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "cts_opportunities.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# List all tables
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", tables)

if "leads" in [t[0] for t in tables]:
    # Show schema
    schema = cur.execute("PRAGMA table_info(leads)").fetchall()
    print("\nSchema for 'leads':")
    for col in schema:
        print(col)

    # Count records
    count = cur.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    print(f"\nTotal records in 'leads': {count}")
else:
    print("\nNo 'leads' table found.")

conn.close()
