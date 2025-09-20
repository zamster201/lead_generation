import requests
import os
import sys

def fetch_summary(opportunity_id: str, api_key: str) -> str:
    url = f"https://api.sam.gov/prod/opportunities/v2/opportunities/{opportunity_id}?api_key={api_key}"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Fetch failed {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    return data.get("description") or data.get("summary") or ""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_fetch_summary.py <opportunity_id>")
        sys.exit(1)

    opp_id = sys.argv[1]
    api_key = os.getenv("SAM_API_KEY") or os.getenv("SAM_API_KEY_1") or os.getenv("SAM_API_KEY_2")
    if not api_key:
        raise RuntimeError("No SAM_API_KEY found in environment")

    text = fetch_summary(opp_id, api_key)
    print(f"--- Summary for {opp_id} ---")
    print(text[:1000])  # first 1000 chars
