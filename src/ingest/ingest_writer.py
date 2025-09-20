import os
import json
import sqlite3
from datetime import datetime
import uuid

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # project root
LEADS_DIR = os.path.join(BASE_DIR, "leads")
DB_PATH = os.path.join(BASE_DIR, "data", "leads.db")

os.makedirs(LEADS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# --- DB init ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            title TEXT,
            agency TEXT,
            posted TEXT,
            due TEXT,
            keywords TEXT,
            value_estimate TEXT,
            source TEXT,
            created TEXT,
            edited TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Writer ---
def write_lead(lead: dict):
    """
    Write lead into JSON, Markdown, and SQLite.
    """

    lead_id = str(uuid.uuid4())
    created_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    edited_ts = created_ts

    lead["id"] = lead_id
    lead["created"] = created_ts
    lead["edited"] = edited_ts

    # --- JSON ---
    json_path = os.path.join(LEADS_DIR, f"{lead_id}.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(lead, jf, indent=2)

    # --- Markdown ---
    md_path = os.path.join(LEADS_DIR, f"{lead_id}.md")
    frontmatter = (
        f"---\n"
        f"created: {created_ts}\n"
        f"edited: {edited_ts}\n"
        f"origin: external\n"
        f"source: {lead.get('source','unknown')}\n"
        f"wf_status: unfiled\n"
        f"tags:\n"
        f"  - \"lead\"\n"
        f"  - \"rfp\"\n"
        f"  - \"{lead_id}\"\n"
        f"---\n\n"
    )
    body = (
        f"# {lead.get('title','(no title)')}\n\n"
        f"- **Agency:** {lead.get('agency','Unknown')}\n"
        f"- **Posted:** {lead.get('posted','Unknown')}\n"
        f"- **Due:** {lead.get('due','Unknown')}\n"
        f"- **Keywords:** {', '.join(lead.get('keywords', []))}\n"
        f"- **Source:** {lead.get('source','Unknown')}\n"
        f"- **Value Estimate:** {lead.get('value_estimate','Unknown')}\n"
    )
    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write(frontmatter + body)

    # --- SQLite ---
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO leads
        (id, title, agency, posted, due, keywords, source, value_estimate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead_id,
        lead.get("title", ""),
        lead.get("agency", ""),
        lead.get("posted", ""),
        lead.get("due", ""),
        ",".join(lead.get("keywords", [])),
        lead.get("source", ""),
        lead.get("value_estimate", "")
    ))
    conn.commit()
    conn.close()

    print(f"✅ Wrote lead {lead_id} → JSON, MD, DB")

# --- Reader ---
def read_leads():
    """Return all leads from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads")
    rows = cursor.fetchall()
    conn.close()
    return rows
