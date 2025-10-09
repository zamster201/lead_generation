
CT Shim — SAM.gov → SQLite → Exports
====================================

Files in this folder:
- ct_shim_sam_to_sqlite_exports.py
- README_ct_shim.txt

Quick start (PowerShell)
------------------------
# IMPORTANT: set your API key as an **environment variable**, not a local variable
$env:SAM_API_KEY = "YOUR_KEY"

# Optional filters
$env:CT_QUERY       = "zero trust"
$env:CT_POSTED_FROM = "2025-08-01"
$env:CT_POSTED_TO   = "2025-08-26"
$env:CT_LIMIT       = "100"

# Run
python ct_shim_sam_to_sqlite_exports.py

Outputs
-------
- SQLite DB: leads.db  (override with $env:CT_DB_PATH)
- Exports folder: .\exports
  - leads_<date>.xlsx
  - leads_<date>.csv
  - md_<date>\<ct_id>.md  (one note per lead)

Notes
-----
- If you previously did:   $SAM_API_KEY = "xxxx"   (without $env:), Excel/Python won't see it.
  Use environment variables (prefix with $env:) so child processes inherit the key.
- The shim auto-populates ct_id and active, and stores any detected document URLs in a 'documents' table.
- Extend to SEWP/NITAAC by adding fetch_* and normalize_* functions mapping into the same leads schema.
