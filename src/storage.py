import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

# Database path (in project root)
db_path = os.path.join(os.path.dirname(__file__), '..', 'leads.db')

def init_db() -> None:
    """Initialize SQLite DB and create leads table if not exists."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            sam_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            naics TEXT,
            soc TEXT,
            point_of_contact TEXT,
            response_deadline TEXT,
            posted_date TEXT,
            link TEXT,
            parsed_doc_text TEXT,
            desc_url TEXT,
            attach_url TEXT,
            fit_score REAL DEFAULT 0.0,
            risk_score REAL DEFAULT 0.0,
            triaged BOOLEAN DEFAULT 0,
            triaged_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(f"DB initialized at {db_path}")

def upsert_lead(lead: Dict) -> None:
    """Upsert lead by sam_id; update scores/triaged if present."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT OR REPLACE INTO leads (
            sam_id, title, description, naics, soc, point_of_contact,
            response_deadline, posted_date, link, parsed_doc_text,
            desc_url, attach_url, fit_score, risk_score, triaged, triaged_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        lead.get('sam_id'),
        lead.get('title'),
        lead.get('description'),
        lead.get('naics'),
        lead.get('soc'),
        lead.get('point_of_contact'),
        lead.get('response_deadline'),
        lead.get('posted_date'),
        lead.get('link'),
        lead.get('parsed_doc_text'),
        lead.get('desc_url'),
        lead.get('attach_url'),
        lead.get('fit_score', 0.0),
        lead.get('risk_score', 0.0),
        lead.get('triaged', False),
        lead.get('triaged_at'),
        now
    ))
    conn.commit()
    conn.close()
    print(f"Upserted lead {lead.get('sam_id')}")

def query_leads(since: Optional[str] = None, triaged_only: bool = False) -> List[Dict]:
    """Query leads; optional since date or triaged filter. Returns list of dicts."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    where_clauses = []
    params = []
    if since:
        where_clauses.append("posted_date >= ?")
        params.append(since)
    if triaged_only:
        where_clauses.append("triaged = 1")
    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    cursor.execute(f"SELECT * FROM leads{where_sql} ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    leads = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return leads

# Test stub
if __name__ == "__main__":
    init_db()
    # Mock upsert
    mock_lead = {"sam_id": "test_123", "title": "Test Lead", "description": "Test desc"}
    upsert_lead(mock_lead)
    print(f"Queried leads: {query_leads()}")