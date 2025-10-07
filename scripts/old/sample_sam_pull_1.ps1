# test_keyword_pull.ps1
# Run a limited keyword-gated pull from SAM.gov

$PythonExe = "C:\CTS\Lead_Generation\.venv\Scripts\python.exe"
$Pipeline  = "C:\CTS\Lead_Generation\src\cts_opps_pipeline.py"

$from = "2025-07-01"    # <-- change this window as you like
$to   = "2025-09-01"

& $PythonExe $Pipeline `
    --profile prod `
    --from $from --to $to `
    --limit 500 `
    --require-keyword-match `
    --db C:\CTS\Lead_Generation\data\cts_opportunities.db `
    --filters-config C:\CTS\Lead_Generation\configs\leadgen.cfg `
    --export-dir E:\LeadGen\Logs --overwrite-exports true --csv --ndjson
