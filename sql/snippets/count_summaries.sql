-- Count total opportunities and breakdown of summary availability
SELECT COUNT(*) AS total,
       SUM(CASE WHEN summary IS NOT NULL AND TRIM(summary) != '' THEN 1 ELSE 0 END) AS with_summary,
       SUM(CASE WHEN summary IS NULL OR TRIM(summary) = '' THEN 1 ELSE 0 END) AS without_summary
FROM opportunities;
