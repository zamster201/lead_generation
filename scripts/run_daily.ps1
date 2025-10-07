# ClearTrend Lead Gen Daily Run
$ErrorActionPreference = "Stop"

# Load env var from profile
$env:SAM_API_KEY = $YourSAMKeyVar  # Your setup

python leadgen_pipeline.py

Write-Output "Run complete: $(Get-Date)"