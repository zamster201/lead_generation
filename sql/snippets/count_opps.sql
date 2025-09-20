-- Total opportunities in DB
SELECT COUNT(*) AS total FROM opportunities;

-- Count opportunities inserted during your last run
-- (replace with actual run dates from your args)
SELECT COUNT(*) AS inserted
FROM opportunities
WHERE posted_date BETWEEN '2025-01-01' AND '2025-01-15';
