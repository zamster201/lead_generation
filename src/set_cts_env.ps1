$env:SAM_API_KEY = "YOUR_KEY"

$env:CTS_QUERY       = '("Kove" OR "software defined memory" OR "memory virtualization") AND ("government" OR "federal" OR "defense" OR "DoD" OR "mission systems") AND ("cost avoidance" OR "upgrade deferral" OR "sustainability" OR "green compute" OR "energy efficiency" OR "national security")'
$env:CTS_POSTED_FROM = "2025-08-01"
$env:CTS_POSTED_TO   = "2025-08-26"
$env:CTS_LIMIT       = "200"

$env:CTS_SEWP_FILE   = "C:\CTS\Lead_Generation\data\sewp_export.xlsx"
$env:CTS_NITAAC_FILE = "C:\CTS\Lead_Generation\data\nitaac_export.csv"

$env:CTS_DB_PATH     = "C:\CTS\Lead_Generation\leads.db"
$env:CTS_EXPORT_DIR  = "C:\CTS\Lead_Generation\exports"

python cts_shim_multi_sources.py
