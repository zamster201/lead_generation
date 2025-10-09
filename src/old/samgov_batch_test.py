import os
import requests
from datetime import datetime
from ingest import ingest_writer

API_KEY = os.getenv("SAM_API_KEY")
BASE_URL = "https://api.sam.gov/prod/opportunities/v2/search"

# Config
query_keyword = "AI"
date_from = "07/20/2025"
date_to = "08/19/2025"

params = {
    "api_key": API_KEY,
    "q": query_keyword,
    "postedFrom": date_from,
    "postedTo": date_to,
    "limit": 5
}

def normalize_date(date_str):
    """Convert MM/DD/YYYY → YYYY-MM-DD, fallback to None if invalid"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
    except Exception:
        return None

resp = requests.get(BASE_URL, params=params)
print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    for opp in data.get("opportunitiesData", []):
        title = opp.get("title", "Untitled")
        agency = opp.get("agency", {}).get("name", "Unknown")

        posted_date = normalize_date(opp.get("postedDate"))
        due_date = normalize_date(opp.get("responseDate", {}).get("dueDate"))

        description = opp.get("description", "")

        # Keywords: use provided OR fallback to query keyword
        keywords = opp.get("keywords", [])
        if not keywords and query_keyword.lower() in description.lower():
            keywords = [query_keyword]

        print(f"✅ {title[:40]}...")
        print(f"   agency: {agency}")
        print(f"   posted: {posted_date if posted_date else 'Unknown'}")
        print(f"   due: {due_date if due_date else 'None'}")
        print(f"   keywords: {keywords}\n")

        # Save normalized lead
        ingest_writer.write_lead({
            "title": title,
            "agency": agency,
            "posted_date": posted_date,
            "due_date": due_date,
            "keywords": keywords,
            "source": "sam.gov"
        })
else:
    print(f"❌ Error: {resp.status_code} {resp.text}")
