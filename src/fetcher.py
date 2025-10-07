import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import tomllib
from parser import parse_attachment  # Chain to parse

# Load config
with open("../configs/leadgen.toml", "rb") as f:
    config = tomllib.load(f)

def fetch_sam_opps(limit: int = None, posted_from: str = None, parse_attachments: bool = False) -> List[Dict]:
    limit = limit or config["api"]["limit"]
    posted_from = posted_from or config["api"]["posted_from"]
    api_key = os.getenv("SAM_API_KEY")
    if not api_key:
        # Mock with fake attachment URL
        mock_attach = "https://example.gov/mock_rfp.pdf"  # Replace with real for tests
        return [
            {
                "id": f"mock_{i}",
                "title": f"ClearTrend RFP {i}",
                "description": f"Seek solutions (strict match test).",
                "naics": config["filters"]["naics_codes"][i % len(config["filters"]["naics_codes"])],
                "typeOfSetAside": "Small Business" if i % 2 == 0 else "",
                "pointOfContactInformation": [{"pointOfContactFullName": f"POC {i}"}],
                "responseDeadLine": (datetime.now() + timedelta(days=40 + i*5)).strftime('%Y-%m-%d'),
                "postedDate": datetime.now().strftime('%Y-%m-%d'),
                "attachmentUrl": mock_attach if i % 3 == 0 else None  # Mock selective attachments
            }
            for i in range(limit)
        ]
    url = "https://api.sam.gov/prod/opportunities/v2/search"
    params = {"limit": limit, "postedFrom": posted_from, "sort": "-updatedDate"}
    headers = {"api-key": api_key}
    try:
        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        opps = data.get("opportunitiesData", [])
        if parse_attachments:
            for opp in opps:
                attach_url = opp.get("attachmentUrl")  # Or attachments[0].url if array
                if attach_url:
                    opp["parsed_doc_text"] = parse_attachment(attach_url)
        return opps
    except Exception as e:
        print(f"SAM fetch error: {e}")
        return []

def map_to_lead(item: Dict) -> Dict:
    return {
        "sam_id": item.get("id"),
        "title": item.get("title", ""),
        "description": item.get("solicitationNumber", "") + " " + item.get("description", ""),
        "naics": item.get("naics", ""),
        "soc": item.get("typeOfSetAside", ""),
        "point_of_contact": item.get("pointOfContactInformation", [{}])[0].get("pointOfContactFullName", ""),
        "response_deadline": item.get("responseDeadLine"),
        "posted_date": item.get("postedDate"),
        "link": f"https://sam.gov/opp/{item.get('id')}",
        "parsed_doc_text": item.get("parsed_doc_text", "")  # From fetch if enabled
    }

# Test stub
if __name__ == "__main__":
    opps = fetch_sam_opps(parse_attachments=True)
    print(len(opps), "opps fetched with optional parses")