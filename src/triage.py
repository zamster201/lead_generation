import os
import json
from typing import List, Dict
import tomllib
from datetime import datetime, timedelta  # For date calcs

# Load config with robust path (works for direct run or import)
config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'leadgen.toml')
with open(config_path, "rb") as f:
    config = tomllib.load(f)

# Interpolate env vars (handles multiple if needed)
def interpolate_env(val):
    if isinstance(val, str) and '$env:' in val:
        env_key = val.split('$env:')[1].split()[0]  # Extract key like 'SAM_API_KEY_1'
        return os.environ.get(env_key, val)  # Fallback to literal if env var missing
    return val

# Apply to the config dict recursively (simple version for your sections)
for section in config:
    for key, value in config[section].items():
        config[section][key] = interpolate_env(value)

from src.scorer import should_triage, fit_score, risk_score  # For triage logic
from src.storage import init_db, upsert_lead, query_leads  # Assuming DB integration

def query_triagable(since_date: str = None) -> List[Dict]:
    """Query leads that are triagable (not yet triaged) since a date (default: last 7 days)."""
    if since_date is None:
        since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    # Use storage query for non-triaged leads
    all_leads = query_leads(since=since_date, triaged_only=False)
    triagable = [lead for lead in all_leads if not lead.get('triaged', False)]
    return triagable

def triaged_leads(leads: List[Dict]) -> List[Dict]:
    """Filter and score leads, return only those that should be triaged."""
    triaged = []
    for lead in leads:
        if should_triage(lead):
            lead['fit_score'] = fit_score(lead.get('description', '') + ' ' + lead.get('parsed_doc_text', ''), config['filters']['keywords'])
            lead['risk_score'] = risk_score(lead)
            lead['triaged'] = True
            lead['triaged_at'] = datetime.now().isoformat()
            triaged.append(lead)
    return triaged

def write_triage(triaged: List[Dict], output_file: str = None) -> str:
    """Write triaged leads to JSON file (default: triaged_leads.json in root)."""
    if output_file is None:
        output_file = os.path.join(os.path.dirname(__file__), '..', 'triaged_leads.json')
    # Upsert to DB first
    for lead in triaged:
        upsert_lead(lead)
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(triaged, f, indent=2, default=str)
    return output_file

# Test stub
if __name__ == "__main__":
    from src.fetcher import fetch_sam_opps, map_to_lead
    opps = fetch_sam_opps(limit=3)
    leads = [map_to_lead(opp) for opp in opps]
    triaged = triaged_leads(leads)
    print(f"{len(triaged)} triaged leads")
    output = write_triage(triaged)
    print(f"Wrote to {output}")
    triagable = query_triagable()
    print(f"Queried {len(triagable)} triagable leads")