import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def mock_results(site_name, num=5):
    """Mock data for offline testing."""
    return [
        {
            'title': f'{site_name} Mock RFP {i}',
            'description': f'Opportunity involving {KEYWORDS[i % len(KEYWORDS)]} for tech integration.',
            'deadline': datetime.now().strftime('%Y-%m-%d'),
            'link': f'https://mock.gov/opp/{i}',
            'posted_date': '2025-10-01'
        }
        for i in range(num)
    ]

def export_results(results, filename):
    """Export to CSV or JSON."""
    df = pd.DataFrame(results)
    if OUTPUT_FORMAT == 'csv':
        df.to_csv(f'outputs/{filename}.csv', index=False)
        logger.info(f'Exported {len(results)} results to CSV')
    else:
        with open(f'outputs/{filename}.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f'Exported {len(results)} results to JSON')