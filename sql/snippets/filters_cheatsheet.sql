-- =========================================
-- CTS Leads Post-Filter Cheat Sheet
-- Save as: filters_cheatsheet.sql
-- =========================================

-- 0) Show schema
SELECT name, sql FROM sqlite_master WHERE type='table';

-- 1) Count total leads
SELECT COUNT(*) AS total_leads FROM leads;

-- 2) Leads with Kove + Federal
SELECT id, cts_id, title, agency, posted, due
FROM leads
WHERE (title || ' ' || notes || ' ' || keywords) LIKE '%Kove%'
  AND (title || ' ' || notes || ' ' || keywords) LIKE '%federal%';

-- 3) Boolean block simulation
-- Memory terms AND Government terms AND Benefit terms
SELECT id, cts_id, title, agency, posted, due
FROM leads
WHERE (
        (title || ' ' || notes || ' ' || keywords) LIKE '%Kove%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%software defined memory%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%memory virtualization%'
      )
  AND (
        (title || ' ' || notes || ' ' || keywords) LIKE '%government%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%federal%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%defense%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%DoD%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%mission systems%'
      )
  AND (
        (title || ' ' || notes || ' ' || keywords) LIKE '%cost avoidance%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%upgrade deferral%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%sustainability%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%green compute%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%energy efficiency%'
     OR (title || ' ' || notes || ' ' || keywords) LIKE '%national security%'
      );

-- 4) Show only Active leads
SELECT id, cts_id, title, agency, posted, due
FROM leads
WHERE active='Active';

-- 5) Leads due within next 30 days
SELECT id, cts_id, title, due
FROM leads
WHERE DATE(due) BETWEEN DATE('now') AND DATE('now','+30 day');

-- 6) Top agencies by lead count
SELECT agency, COUNT(*) AS count
FROM leads
GROUP BY agency
ORDER BY count DESC
LIMIT 10;

-- 7) Join leads with documents (show first doc URL per lead)
SELECT l.id, l.cts_id, l.title, substr(MIN(d.url),1,120) AS sample_url
FROM leads l
LEFT JOIN documents d ON l.id = d.lead_id
GROUP BY l.id
ORDER BY l.posted DESC;
