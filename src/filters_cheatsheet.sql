-- =========================================
-- CTS Leads Post-Filter Cheat Sheet
-- Location: CTS:\Lead_Generation\src\filters_cheatsheet.sql
-- =========================================

-- 1) Count total leads
SELECT COUNT(*) AS total_leads FROM leads;

-- 2) Leads with Kove + Federal
SELECT id, title, agency, posted, due
FROM leads
WHERE (title || ' ' || notes || ' ' || keywords) LIKE '%Kove%'
  AND (title || ' ' || notes || ' ' || keywords) LIKE '%federal%';

-- 3) Boolean block simulation
-- Memory terms
-- Government terms
-- Benefit terms
SELECT id, title, agency, posted, due
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
SELECT id, title, agency, posted, due
FROM leads
WHERE active='Active';

-- 5) Leads due within next 30 days
SELECT id, title, due
FROM leads
WHERE DATE(due) BETWEEN DATE('now') AND DATE('now','+30 day');

-- 6) Top agencies by lead count
SELECT agency, COUNT(*) AS count
FROM leads
GROUP BY agency
ORDER BY count DESC
LIMIT 10;
