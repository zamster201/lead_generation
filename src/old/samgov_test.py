import requests
import json
import os
from datetime import date, timedelta

# 🔑 Replace with your real API key  (Declared in $PROFILE)

API_KEY = os.getenv("SAM_API_KEY")

# Set date range for the last 14 days
end_date = date.today()
start_date = end_date - timedelta(days=14)

# SAM.gov API endpoint
URL = "https://api.sam.gov/prod/opportunities/v1/search"

params = {
    "api_key": API_KEY,
    "limit": 3,  # small test batch
    "postedFrom": start_date.strftime("%Y-%m-%d"),
    "postedTo": end_date.strftime("%Y-%m-%d"),
    "keywords": "cybersecurity"
}

def main():
    print(f"Querying SAM.gov from {params['postedFrom']} to {params['postedTo']} with keyword {params['keywords']}...")

    response = requests.get(URL, params=params)

    if response.status_code == 200:
        data = response.json()
        # Print summary of first few opportunities
        for opp in data.get("opportunitiesData", []):
            print("\n---")
            print("Title:", opp.get("title"))
            print("Agency:", opp.get("agency"))
            print("Due Date:", opp.get("responseDate"))
            print("Solicitation #:", opp.get("solicitationNumber"))
            print("URL:", opp.get("uiLink"))
        print("\n✅ API call successful.")
    else:
        print("❌ Error:", response.status_code, response.text)

if __name__ == "__main__":
    main()
