-- ==============================================
-- Show the most recent 5 opportunities inserted
-- ==============================================

SELECT
    id,
    opportunity_id,
    title,
    agency,
    posted_date,
    due_date,
    est_value,
    substr(summary_text, 1, 300) AS summary_preview
FROM opportunities
ORDER BY id DESC
LIMIT 5;
