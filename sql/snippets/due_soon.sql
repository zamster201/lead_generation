-- Opportunities due within 14 days
SELECT opportunity_id, title, due_date, fit_score, portfolio
FROM opportunities
WHERE due_date IS NOT NULL
  AND date(due_date) <= date('now', '+14 days')
ORDER BY due_date ASC;
