import pandas as pd
from config import KEYWORDS, SITES, MATCH_THRESHOLD
from query_sites import QUERY_FUNCS
from matcher import filter_opportunities
from utils import export_results, logger

def main():
    all_results = []
    for site_name, config in SITES.items():
        if site_name in QUERY_FUNCS:
            results = QUERY_FUNCS[site_name](config)
            all_results.extend(results)
    
    # Match and filter
    matched = filter_opportunities(all_results, MATCH_THRESHOLD)
    
    # Export
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    export_results(matched, f'opportunities_{timestamp}')
    
    # Summary
    logger.info(f'Found {len(matched)} applicable opportunities for {len(KEYWORDS)} keywords')
    for opp in matched[:3]:  # Top 3 preview
        logger.info(f"- {opp['title']} (Score: {opp['relevance_score']:.1f}): {opp['link']}")

if __name__ == '__main__':
    main()