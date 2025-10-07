sqlite3 C:\CTS\Lead_Generation\data\cts_opportunities.db "SELECT title, substr(summary,1,120) FROM opportunities WHERE summary IS NOT NULL AND TRIM(summary) != '' LIMIT 5;"
