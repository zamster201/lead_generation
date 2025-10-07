import json
from datetime import datetime
from pathlib import Path
import sqlite3
import pandas as pd
import tomllib
from typing import Dict, List  # Added for Dict type hints
from scorer import should_triage

# Load config (explicit for this module)
with open("../configs/leadgen.toml", "rb") as f:
    config = tomllib.load(f)
MIN_DAYS_TO_DUE = config["filters"]["min_days_to_due"]
FIT_THRESHOLD = config["filters"]["fit_threshold"]
RISK_THRESHOLD = config["filters"]["risk_threshold"]

OUTPUT_DIR = "../outputs"

def write_triage(leads: List[Dict]):
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    md_path = Path(OUTPUT_DIR) / f"Daily_Triage_{today}.md"
    json_path = Path(OUTPUT_DIR) / f"triage_{today}.json"

    triaged = [l for l in leads if should_triage(l["fit_score"], l["risk_score"], l["days_to_due"])]

    with open(md_path, "w") as f:
        f.write(f"# ClearTrend Daily Triage - {today}\n\n")
        f.write(f"**{len(triaged)} high-fit opportunities.**\n\n")
        for lead in sorted(triaged, key=lambda x: x["fit_score"], reverse=True):
            f.write(f"## {lead['title']} (Fit: {lead['fit_score']:.0f}, Risk: {lead['risk_score']:.0f}, Days: {lead['days_to_due']})\n")
            f.write(f"**Status:** {lead['status_stage']} | **POC:** {lead['point_of_contact']}\n\n")
            f.write(f"{lead['description'][:300]}...\n\n")
            f.write(f"[SAM Link]({lead['link']})\n\n---\n")

    with open(json_path, "w") as f:
        json.dump({"timestamp": today, "leads": triaged}, f, indent=2)

    print(f"Triage saved: {md_path} ({len(triaged)} leads)")

def query_triagable() -> List[Dict]:
    conn = sqlite3.connect("../opps.db")
    df = pd.read_sql_query("""
        SELECT * FROM opportunities
        WHERE days_to_due >= ? AND fit_score >= ? AND risk_score <= ?
    """, conn, params=(MIN_DAYS_TO_DUE, FIT_THRESHOLD, RISK_THRESHOLD))
    conn.close()
    return df.to_dict("records")

# Test stub
if __name__ == "__main__":
    # Mock leads for write_triage test
    mock_leads = [{"fit_score": 80, "risk_score": 40, "days_to_due": 35, "title": "Test Lead", "status_stage": "new", "point_of_contact": "POC", "description": "Test desc", "link": "test.link"}]
    write_triage(mock_leads)