import hashlib
import sqlite3
from typing import Dict

DB_PATH = "../opps.db"  # Relative from src/

def compute_rev_hash(lead: Dict) -> str:
    content = f"{lead['title']}{lead['description']}{lead['response_deadline']}"
    return hashlib.sha256(content.encode()).hexdigest()

def has_changed(conn: sqlite3.Connection, lead: Dict) -> bool:
    rev_hash = compute_rev_hash(lead)
    cursor = conn.cursor()
    existing = cursor.execute("SELECT rev_hash FROM opportunities WHERE sam_id = ?", (lead["sam_id"],)).fetchone()
    return not existing or existing[0] != rev_hash

# Test stub: if __name__ == "__main__": print(compute_rev_hash({"title": "Test"}))