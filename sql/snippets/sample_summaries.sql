-- Show 5 samples with their summaries
SELECT opportunity_id, title, substr(summary, 1, 120) AS preview
FROM opportunities
WHERE summary IS NOT NULL AND TRIM(summary) != ''
LIMIT 5;
