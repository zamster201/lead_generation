import os
import requests
import uuid
from datetime import datetime

# === Config ===
api_key = os.getenv("SAM_API_KEY")
url = "https://api.sam.gov/prod/opportunities/v2/search"
params = {
    "limit": 1,
    "postedFrom": "08/01/2025",
    "postedTo": "08/18/2025",
    "api_key": api_key
}

# === Query API ===
resp = requests.get(url, params=params)
if resp.status_code != 200:
    print(f"❌ Error {resp.status_code}: {resp.text}")
    exit()

data = resp.json()
opp = data.get("opportunitiesData", [])[0] if data.get("opportunitiesData") else None

if not opp:
    print("⚠️ No opportunities found in given range.")
    exit()

# === Transform into Lead shape ===
lead = {
    "uid": str(uuid.uuid4())[:8],
    "title": opp.get("title", "Untitled RFP"),
    "agency": opp.get("agency", "Unknown"),
    "due_date": opp.get("responseDate"),
    "keywords": opp.get("naics", []),  # fallback: NAICS codes
    "value_estimate": opp.get("awardAmount", "N/A"),
    "retrieved": datetime.now().isoformat(timespec="seconds")
}

# === Print lead ===
print("✅ Retrieved lead:")
for k, v in lead.items():
    print(f"  {k}: {v}")
