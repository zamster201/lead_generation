import sqlite3
from typing import Dict
from scorer import compute_days_to_due, fit_score, risk_score  # Cross-import ok for modularity
from detector import compute_rev_hash  # Added: Import for rev_hash func

DB_PATH = "../opps.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            sam_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            naics TEXT,
            soc TEXT,
            point_of_contact TEXT,
            response_deadline TEXT,
            days_to_due INTEGER,
            posted_date TEXT,
            link TEXT,
            rev_hash TEXT,
            fit_score REAL DEFAULT 0,
            risk_score REAL DEFAULT 0,
            status_stage TEXT DEFAULT 'new'
        )
    """)
    conn.commit()
    conn.close()

def upsert_lead(conn: sqlite3.Connection, lead: Dict):
    days_to_due = compute_days_to_due(lead["response_deadline"])
    fit = fit_score(lead["title"], lead["description"], lead["naics"])
    risk = risk_score(lead["soc"], days_to_due)
    rev_hash = compute_rev_hash(lead)  # Now imported
    lead.update({"days_to_due": days_to_due, "fit_score": fit, "risk_score": risk, "rev_hash": rev_hash})

    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO opportunities
        (sam_id, title, description, naics, soc, point_of_contact, response_deadline,
         days_to_due, posted_date, link, rev_hash, fit_score, risk_score, status_stage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT status_stage FROM opportunities WHERE sam_id = ?), 'new'))
    """, (lead["sam_id"], lead["title"], lead["description"], lead["naics"], lead["soc"],
          lead["point_of_contact"], lead["response_deadline"], days_to_due, lead["posted_date"],
          lead["link"], rev_hash, fit, risk, lead["sam_id"]))
    conn.commit()

# Test stub
if __name__ == "__main__":
    init_db()
    print("DB initialized successfully.")