-- =========================================================
-- Review summaries in the opportunities table
-- =========================================================

-- 1) Count how many opportunities have summaries
SELECT COUNT(*) AS total,
       SUM(CASE WHEN summary IS NOT NULL AND TRIM(summary) != '' THEN 1 ELSE 0 END) AS with_summary,
       SUM(CASE WHEN summary IS NULL OR TRIM(summary) = '' THEN 1 ELSE 0 END) AS without_summary
FROM opportunities;

-- 2) Show 5 sample summaries
SELECT opportunity_id,
       title,
       substr(summary, 1, 200) AS snippet
FROM opportunities
WHERE summary IS NOT NULL AND TRIM(summary) != ''
LIMIT 5;

-- 3) Longest summaries (likely to contain real content)
SELECT opportunity_id,
       title,
       LENGTH(summary) AS length,
       substr(summary, 1, 300) AS snippet
FROM opportunities
WHERE summary IS NOT NULL AND TRIM(summary) != ''
ORDER BY LENGTH(summary) DESC
LIMIT 5;
