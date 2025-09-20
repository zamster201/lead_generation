---
created: 2025-08-26
edited: 2025-08-26
origin: CTS
source: internal
wf_status: unfiled
tags:
  - cts
  - lead_generation
  - ingest
  - runbook
  - "#MSIS"
---

# 🚀 CTS Lead Generation – Initial Ingest Runbook

This runbook describes how to set up and run the **CTS Multi-Source Ingest Shim** (`cts_shim_multi_sources.py`) for the first time.

---
## 1. Prerequisites

- Python 3.11+ installed and in your PATH   
- Required Python packages:

`pip install requests pandas openpyxl`

- Valid **SAM.gov API key** (from api.data.gov).

---

## 2. Directory Layout

Create the following structure:
`CTS\ └── Lead_Generation\     ├── src\     │   ├── cts_shim_multi_sources.py     │   ├── README_cts_shim_multi_sources.txt     │   ├── filters_cheatsheet.sql     │   └── RUNBOOK_initial_ingest.md   # (this file)     ├── data\             # SEWP/NITAAC raw exports     ├── exports\          # CSV/XLSX/MD outputs     └── leads.db          # SQLite database (auto-created)`

---
## 3. First Test (File Only)

Create a small SEWP test file:  
`C:\CTS\Lead_Generation\data\sewp_export.csv`

`"Solicitation Number","Title","Agency","Release Date","Due Date","URL","Description" "SEWP-TEST-001","Edge Compute Refresh","NASA","2025-08-01","2025-09-15","https://sewp.nasa.gov/rfq/SEWP-TEST-001","Specs and SOW: https://example.com/sow.pdf" "SEWP-TEST-002","Secure Storage Upgrade","NOAA","2025-08-05","2025-09-10","https://sewp.nasa.gov/rfq/SEWP-TEST-002","Include FIPS module link at https://example.com/fips.pdf"`

Run:

``cd C:\CTS\Lead_Generation\src  python .\cts_shim_multi_sources.py --no-sam `   --sewp-file "C:\CTS\Lead_Generation\data\sewp_export.csv" `   --db-path "C:\CTS\Lead_Generation\leads.db" `   --export-dir "C:\CTS\Lead_Generation\exports"``

Check outputs:

- `leads.db` created
- `exports\leads_<date>.csv`
- `exports\leads_<date>.xlsx`
- `exports\md_<date>\*.md`    

---

## 4. Enable SAM.gov API

Set your key (PowerShell):

`$env:SAM_API_KEY = "YOUR_API_KEY"
Run a small pull:
``python .\cts_shim_multi_sources.py `   --sam-api-key "$env:SAM_API_KEY" `   --query "cybersecurity" `   --from 2025-08-01 --to 2025-08-26 `   --limit 5 `   --db-path "C:\CTS\Lead_Generation\leads.db" `   --export-dir "C:\CTS\Lead_Generation\exports"``

---

## 5. Full Boolean Query Example

``python .\cts_shim_multi_sources.py `   --sam-api-key "$env:SAM_API_KEY" `   --query '("Kove" OR "software defined memory" OR "memory virtualization") AND ("government" OR "federal" OR "defense" OR "DoD" OR "mission systems") AND ("cost avoidance" OR "upgrade deferral" OR "sustainability" OR "green compute" OR "energy efficiency" OR "national security")' `   --from 2025-08-01 --to 2025-08-26 `   --limit 50 `   --db-path "C:\CTS\Lead_Generation\leads.db" `   --export-dir "C:\CTS\Lead_Generation\exports"``

---

## 6. Validate Results

Quick DB check:

`sqlite3 C:\CTS\Lead_Generation\leads.db "SELECT id, cts_id, source, posted, due FROM leads;"`

Run post-filters:

`sqlite3 C:\CTS\Lead_Generation\leads.db ".read C:\CTS\Lead_Generation\src\filters_cheatsheet.sql"`

---

## 7. What Success Looks Like

- `cts_id` auto-populated like `CTS-SAMGOV-20250801-XXXX`    
- `documents` table filled with URLs from file/API rows
- `.xlsx` opens in Excel with `doc_urls` column
- `.md` files contain Obsidian-friendly frontmatter

---

## 8. Next Steps

- Add NITAAC exports (`--nitaac-file ...`)
- Use **post-filters** (`filters_cheatsheet.sql`) to tighten Boolean matches.
- Later: bolt on **USAspending enrichment** (`ct_awards_enrich.py`).    

---

👉