-- =========================================================
-- Check consistency between DB inserts and pipeline reports
-- =========================================================

-- Total opportunities currently in DB
SELECT COUNT(*) AS total_in_db
FROM opportunities;

-- Count opportunities inserted in a given window
-- 👇 Replace with your run's date window (from args)
SELECT COUNT(*) AS inserted_in_window
FROM opportunities
WHERE posted_date BETWEEN '2025-01-01' AND '2025-01-15';
