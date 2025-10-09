import sqlite3
from sam_client import request_sam, map_sam_item_to_lead
from scoring import fit_score, risk_score, should_triage
from change_detect import upsert_lead, compute_rev_hash
from write_triage import write_daily_triage
import configparser
import os

# Init DB
conn = sqlite3.connect('opps.db')
with open('src/opportunities_schema.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()

config = configparser.ConfigParser()
config.read('configs/leadgen.cfg')
limit = int(config['filters']['limit'])

# Fetch & Process
raw_opps = request_sam(limit=limit)
leads = [map_sam_item_to_lead(item) for item in raw_opps]

conn = sqlite3.connect('opps.db')
updated_count = 0
for lead in leads:
    if not lead['sam_id']: continue
    scores = {
        'fit': fit_score(lead['title'], lead['description'], lead['naics']),
        'risk': risk_score(lead['soc'], lead['days_to_due'])
    }
    if should_triage(scores['fit'], scores['risk'], lead['days_to_due']):
        if upsert_lead(conn, lead, scores):
            updated_count += 1

conn.close()
print(f"Processed {len(leads)} opps, updated {updated_count}")

# Triage
write_daily_triage()