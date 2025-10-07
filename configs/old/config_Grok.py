# Keyword set - replace with yours (e.g., for tech portfolio: AI, ML, cloud, cybersecurity)
KEYWORDS = [
    "artificial intelligence", "machine learning", "cloud computing", "cybersecurity",
    "data analytics", "blockchain", "IoT", "software development"
]

# Sites config: dict of {name: {'url': , 'api_endpoint': , 'params': , 'auth': }}
SITES = {
    'sam_gov': {  # Federal contracts/RFPs
        'base_url': 'https://api.sam.gov',
        'endpoint': '/opportunities/v2/search',  # Example API; check docs for keys
        'params': {'limit': 50, 'postedFrom': '2025-01-01'},  # Customize dates
        'auth': {'api_key': 'YOUR_SAM_API_KEY'}  # Get free key from SAM.gov
    },
    'grants_gov': {  # Grants/studies
        'base_url': 'https://www.grants.gov',
        'endpoint': '/search-results',  # Web search; use scraping for now
        'params': {'keywords': ' '.join(KEYWORDS)},  # Placeholder
        'auth': None
    },
    # Add more: e.g., 'beta_sam_dun': {'url': 'https://beta.sam.gov/...'}
}

# Matching threshold: 70% similarity for "applicable" opportunities
MATCH_THRESHOLD = 70
OUTPUT_FORMAT = 'csv'  # or 'json'