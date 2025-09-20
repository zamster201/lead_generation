-- Show opportunities with keyword hits
SELECT opportunity_id, title, portfolio, keyword_hits
FROM opportunities
WHERE keyword_hits IS NOT NULL AND TRIM(keyword_hits) != ''
LIMIT 20;
