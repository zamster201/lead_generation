import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import tomllib
from src.parser import parse_attachment  # Chain to parse

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

def fetch_sam_opps(limit: int = None, posted_from: str = None, posted_to: str = None, parse_attachments: bool = False) -> List[Dict]:
    limit = limit or config["api"]["limit"]
    posted_from = posted_from or config["api"]["posted_from"]
    posted_to = posted_to or config["api"]["posted_to"]
    api_key = config['sam_api']['api_key']
    if not api_key or api_key.startswith('$env:'):
        # Mock data matching real flat schema
        mock_attach = "https://example.gov/mock_rfp.pdf"
        mock_naics = config["filters"]["naics_codes"]
        today = datetime.now()
        return [
            {
                "noticeId": f"mock_{i}",
                "title": f"ClearTrend RFP {i}",
                "description": f"https://api.sam.gov/prod/opportunities/v1/noticedesc?noticeid=mock_{i}&api_key={api_key}",  # Mock desc URL
                "naicsCode": mock_naics[i % len(mock_naics)],
                "typeOfSetAside": "SBA" if i % 2 == 0 else None,
                "pointOfContact": [{"fullName": f"POC {i}", "type": "primary", "email": f"poc{i}@example.com"}],
                "responseDeadLine": (today + timedelta(days=40 + i*5)).strftime('%Y-%m-%d %H:%M:%S') if i % 2 else None,
                "postedDate": today.strftime('%Y-%m-%d'),
                "resourceLinks": [mock_attach] if i % 3 == 0 else [],
                "solicitationNumber": f"SOL-{i:04d}",
            }
            for i in range(limit)
        ]

    # Real API call
    url = "https://api.sam.gov/prod/opportunities/v2/search"
    params = {
        "limit": limit,
        "postedFrom": posted_from,  # MM/dd/yyyy
        "postedTo": posted_to,      # MM/dd/yyyy
        "api_key": api_key
    }
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        opps = data.get("opportunitiesData", [])
        if parse_attachments:
            for opp in opps:
                resource_links = opp.get("resourceLinks", [])
                attach_url = resource_links[0] if resource_links else None
                if attach_url:
                    try:
                        opp["parsed_doc_text"] = parse_attachment(attach_url)
                    except Exception as parse_err:
                        print(f"Parse error for {attach_url}: {parse_err}")
                        opp["parsed_doc_text"] = ""
                # Optionally fetch description text from desc URL
                desc_url = opp.get("description")
                if desc_url and "?api_key=" not in desc_url:
                    desc_url += f"&api_key={api_key}"  # Append if missing
                    try:
                        desc_resp = requests.get(desc_url)
                        desc_resp.raise_for_status()
                        opp["description_text"] = desc_resp.text
                    except Exception as desc_err:
                        print(f"Desc fetch error for {desc_url}: {desc_err}")
                        opp["description_text"] = ""
        return opps
    except Exception as e:
        print(f"SAM fetch error: {e}")
        return []

def map_to_lead(item: Dict) -> Dict:
    poc_list = item.get("pointOfContact", [{}])
    point_of_contact = poc_list[0].get("fullName", "") if poc_list else ""
    desc_text = item.get("description_text", "")  # From fetch if enabled
    resource_links = item.get("resourceLinks", [])
    desc_url = item.get("description", "")  # URL for desc
    attach_url = resource_links[0] if resource_links else ""
    return {
        "sam_id": item.get("noticeId"),
        "title": item.get("title", ""),
        "description": item.get("solicitationNumber", "") + " " + desc_text,
        "naics": item.get("naicsCode", ""),
        "soc": item.get("typeOfSetAside", ""),
        "point_of_contact": point_of_contact,
        "response_deadline": item.get("responseDeadLine"),
        "posted_date": item.get("postedDate"),
        "link": f"https://sam.gov/opp/{item.get('noticeId')}",
        "parsed_doc_text": item.get("parsed_doc_text", ""),
        "desc_url": desc_url,
        "attach_url": attach_url  # First attachment
    }

# Test stub
if __name__ == "__main__":
    opps = fetch_sam_opps(parse_attachments=True)
    leads = [map_to_lead(opp) for opp in opps]
    print(f"{len(leads)} leads fetched and mapped with optional parses")
    for lead in leads[:2]:  # Print first two for preview
        print(lead)