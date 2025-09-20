-- Count opportunities by portfolio
SELECT portfolio, COUNT(*) AS count
FROM opportunities
GROUP BY portfolio
ORDER BY count DESC;
