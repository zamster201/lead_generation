# daily_incremental.ps1
# Defaulted daily incremental pull (yesterday -> today) for SAM.gov

# --- Config ---
$PythonExe = "C:\CTS\Lead_Generation\.venv\Scripts\python.exe"
$Pipeline  = "C:\CTS\Lead_Generation\src\cts_opps_pipeline.py"
$Runlog    = "E:\Tools\write_runlog.py"

# --- Dates ---
$from = (Get-Date).AddDays(-1).ToString('yyyy-MM-dd')
$to   = (Get-Date).ToString('yyyy-MM-dd')

# --- Run pipeline (defaults: prod key, default query, default paths) ---
& $PythonExe $Pipeline `
    --from $from --to $to `
    --profile prod `
| & $PythonExe $Runlog E:\LeadGen\Logs md
