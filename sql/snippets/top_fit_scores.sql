-- Top 10 opportunities by fit score
SELECT opportunity_id, title, fit_score, risk_score, portfolio
FROM opportunities
ORDER BY fit_score DESC
LIMIT 10;
