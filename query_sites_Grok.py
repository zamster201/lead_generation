import requests
from bs4 import BeautifulSoup
from utils import logger, mock_results

def query_sam_gov(config):
    """Query SAM.gov API for RFPs/contracts."""
    try:
        url = f"{config['base_url']}{config['endpoint']}"
        params = config['params']
        headers = {'api-key': config['auth']['api_key']} if config['auth'] else {}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Parse: adapt based on actual API response (e.g., data['opportunities'])
        results = [
            {
                'title': opp.get('title', ''),
                'description': opp.get('description', ''),
                'deadline': opp.get('pointOfContact', {}).get('responseDeadlineDate', ''),
                'link': opp.get('id', f"https://sam.gov/opp/{opp['id']}"),
                'posted_date': opp.get('postedDate', '')
            }
            for opp in data.get('opportunities', [])
        ]
        logger.info(f'Fetched {len(results)} from SAM.gov')
        return results
    except Exception as e:
        logger.error(f'SAM.gov query failed: {e}')
        return mock_results('sam_gov')  # Fallback

def query_grants_gov(config):
    """Scrape/search Grants.gov (API if available; else BS4)."""
    try:
        url = f"{config['base_url']}{config['endpoint']}"
        params = config['params']
        response = requests.get(url, params=params)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Parse: target actual selectors (e.g., '.search-result-title')
        results = []  # Placeholder: extract from soup.find_all('div', class_='grant-item')
        # Example mock parse:
        for item in soup.find_all('div', class_='mock-grant'):  # Replace with real
            results.append({
                'title': item.find('h3').text if item.find('h3') else '',
                'description': item.find('p').text if item.find('p') else '',
                'deadline': 'TBD',
                'link': item.find('a')['href'] if item.find('a') else '',
                'posted_date': '2025-10-01'
            })
        logger.info(f'Fetched {len(results)} from Grants.gov')
        return results
    except Exception as e:
        logger.error(f'Grants.gov query failed: {e}')
        return mock_results('grants_gov')

# Add more query functions here for other sites
QUERY_FUNCS = {
    'sam_gov': query_sam_gov,
    'grants_gov': query_grants_gov,
}