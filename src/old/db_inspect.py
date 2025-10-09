# db_inspect.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "leads.db"

def show_counts():
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Total leads
    total = cur.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    print(f"📊 Total leads: {total}")

    # Breakdown by agency
    print("\nBy agency:")
    for row in cur.execute("SELECT agency, COUNT(*) FROM leads GROUP BY agency ORDER BY COUNT(*) DESC LIMIT 10"):
        print(f"  {row[0] or 'Unknown'}: {row[1]}")

    # Breakdown by source
    print("\nBy source:")
    for row in cur.execute("SELECT source, COUNT(*) FROM leads GROUP BY source ORDER BY COUNT(*) DESC"):
        print(f"  {row[0]}: {row[1]}")

    conn.close()

if __name__ == "__main__":
    show_counts()
