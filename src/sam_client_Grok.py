import requests
import json
from datetime import datetime

API_KEY = 'YOUR_SAM_API_KEY'  # Replace with your key
BASE_URL = 'https://api.sam.gov/prod/opportunities/v2/search'
HEADERS = {'api-key': API_KEY, 'Content-Type': 'application/json'}

def request_sam(limit=50, posted_from='2025-01-01'):
    """Fetch opportunities from SAM.gov API."""
    params = {
        'limit': limit,
        'postedFrom': posted_from,
        'sort': '-updatedDate'  # Newest first
    }
    try:
        response = requests.get(BASE_URL, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data.get('opportunitiesData', [])
    except Exception as e:
        print(f"SAM fetch error: {e}")
        return []  # Or mock: return [{'title': 'Mock Opp', ...}]

def map_sam_item_to_lead(item):
    """Map SAM item to lead dict."""
    return {
        'sam_id': item.get('id'),
        'title': item.get('title'),
        'description': item.get('solicitationNumber', '') + ' ' + item.get('description', ''),
        'naics': item.get('naics', ''),
        'soc': item.get('typeOfSetAside', ''),
        'point_of_contact': item.get('pointOfContactInformation', [{}])[0].get('pointOfContactFullName', ''),
        'response_deadline': item.get('responseDeadLine'),
        'posted_date': item.get('postedDate'),
        'link': f"https://sam.gov/opp/{item.get('id')}"
    }

# Example for Grants.gov (add to multi-site)
def request_grants_gov(keywords, limit=50):
    """Placeholder for Grants.gov; implement scraping/API."""
    # TODO: Use https://www.grants.gov/xml-extract.html or API
    url = 'https://www.grants.gov/search-results'
    params = {'keywords': ' '.join(keywords), 'limit': limit}
    try:
        response = requests.get(url, params=params)
        # Parse with BS4 (add import if used)
        # For now, mock
        return [{'title': 'Mock Grant', 'description': 'AI research grant', ...}]
    except:
        return []