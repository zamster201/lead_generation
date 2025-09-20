-- =========================================================
-- CT LeadGen Debug Snapshot
-- Runs multiple queries in sequence
-- =========================================================
--
--   sqlite3 C:\CTS\Lead_Generation\data\cts_opportunities.db ".read C:\CTS\Lead_Generation\sql\snippets\group_by_portfolio.sql"
--
--
.echo on

-- 1) Count total vs with/without summary
.read count_summaries.sql

-- 2) Show 5 sample summaries
.read sample_summaries.sql

-- 3) Opportunities grouped by portfolio
.read group_by_portfolio.sql

-- 4) Top 10 opportunities by fit score
.read top_fit_scores.sql

-- 5) Opportunities due soon
.read due_soon.sql

-- 6) Keyword hits
.read keyword_hits.sql

.echo off
