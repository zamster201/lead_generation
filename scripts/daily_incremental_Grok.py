# Daily Incremental Pipeline
$ErrorActionPreference = "Stop"

# Set paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$python = "python"
$pipeline = "$scriptDir/../cts_opps_pipeline.py"

# Run pipeline
& $python $pipeline

# Triage
& $python -c "from src.write_triage import write_daily_triage; write_daily_triage()"

Write-Host "Daily run complete: $(Get-Date)"