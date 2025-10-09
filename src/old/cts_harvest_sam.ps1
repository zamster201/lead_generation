pwsh C:\CTS\Lead_Generation\src\cts_harvest_sam.ps1 `
  -Query 'Kove software defined memory virtualization storage performance' `
  -From '2025-01-01' -To '2025-08-26' `
  -Limit 50 -ThrottleMs 1200 -MaxRetries 5 `
  -DbPath 'C:\CTS\Lead_Generation\leads.db' `
  -ExportDir 'C:\CTS\Lead_Generation\exports'
<# 
cts_harvest_sam.ps1
Harvest SAM.gov in monthly chunks via CTS shim with throttling & retries.

Usage (example):
  pwsh C:\CTS\Lead_Generation\src\cts_harvest_sam.ps1 `
    -Query 'Kove software defined memory virtualization storage performance' `
    -From '2025-01-01' -To '2025-08-26' `
    -Limit 50 -ThrottleMs 1200 -MaxRetries 5 `
    -DbPath 'C:\CTS\Lead_Generation\leads.db' `
    -ExportDir 'C:\CTS\Lead_Generation\exports' `
    -Verbose

Notes:
- The shim already normalizes ISO dates (YYYY-MM-DD) to SAM’s MM/dd/yyyy internally.
- This script pauses between calls to respect ~1 req/sec and honors your shim’s backoff logic.
- You can resume by re-running; the shim upserts on leads.id (no dupes).
#>

param(
  [Parameter(Mandatory=$true)]
  [string]$Query,

  [Parameter(Mandatory=$true)]
  [string]$From,          # ISO ok: 2025-01-01

  [Parameter(Mandatory=$true)]
  [string]$To,            # ISO ok: 2025-08-26

  [int]$Limit = 50,       # per-call cap; smaller = safer
  [int]$ThrottleMs = 1200,# pause after each request (ms)
  [int]$MaxRetries = 5,   # shim-level retries on 429/5xx
  [string]$DbPath = "C:\CTS\Lead_Generation\leads.db",
  [string]$ExportDir = "C:\CTS\Lead_Generation\exports",

  # Optional: pass explicit key; otherwise use $env:SAM_API_KEY
  [string]$SamApiKey = $env:SAM_API_KEY,

  # Path to the shim
  [string]$ShimPath = "C:\CTS\Lead_Generation\src\cts_shim_multi_sources.py",

  # Set this to $true if you only want to ingest files (skip SAM)
  [switch]$NoSam = $false
)

# --- sanity checks ---
if (-not (Test-Path $ShimPath)) {
  throw "Shim not found at $ShimPath"
}
if (-not $NoSam -and [string]::IsNullOrWhiteSpace($SamApiKey)) {
  throw "SAM API key is required (set -SamApiKey or $env:SAM_API_KEY)."
}
if (-not (Test-Path $ExportDir)) { New-Item -ItemType Directory -Path $ExportDir -Force | Out-Null }

# --- parse dates ---
try {
  $start = Get-Date $From
  $end   = Get-Date $To
} catch {
  throw "Invalid date(s). Use ISO like 2025-01-01."
}
if ($start -gt $end) { throw "'From' must be <= 'To'." }

# --- month slicing helper ---
function Get-MonthSlices([datetime]$Start, [datetime]$End) {
  $cursor = Get-Date -Date $Start -Hour 0 -Minute 0 -Second 0
  while ($cursor -le $End) {
    $sliceStart = $cursor
    $sliceEnd = ($cursor.AddMonths(1).AddDays(-1))
    if ($sliceEnd -gt $End) { $sliceEnd = $End }
    [pscustomobject]@{
      From = $sliceStart.ToString("yyyy-MM-dd")
      To   = $sliceEnd.ToString("yyyy-MM-dd")
    }
    $cursor = $sliceEnd.AddDays(1)
  }
}

# --- log header ---
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logPath = Join-Path $ExportDir "sam_harvest_$stamp.log"
"Started: $(Get-Date) | Query=`"$Query`" | Range=$From..$To | Limit=$Limit | ThrottleMs=$ThrottleMs | MaxRetries=$MaxRetries" |
  Tee-Object -FilePath $logPath

# --- run slices ---
$slices = Get-MonthSlices -Start $start -End $end
$idx = 0
foreach ($s in $slices) {
  $idx++
  $msg = "[$idx/$($slices.Count)] Harvesting $($s.From) → $($s.To)"
  Write-Host $msg -ForegroundColor Cyan
  $msg | Tee-Object -FilePath $logPath -Append | Out-Null

  $pythonArgs = @(
    "`"$ShimPath`"",
    "--query", "`"$Query`"",
    "--from", $s.From,
    "--to", $s.To,
    "--limit", $Limit,
    "--db-path", "`"$DbPath`"",
    "--export-dir", "`"$ExportDir`"",
    "--throttle-ms", $ThrottleMs,
    "--max-retries", $MaxRetries,
    "--verbose"
  )
  if (-not $NoSam) {
    $pythonArgs += @("--sam-api-key", "`"$SamApiKey`"")
  } else {
    $pythonArgs += "--no-sam"
  }

  # run shim
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = "python"
  $psi.Arguments = $pythonArgs -join " "
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  $psi.UseShellExecute = $false
  $proc = New-Object System.Diagnostics.Process
  $proc.StartInfo = $psi

  [void]$proc.Start()
  $stdout = $proc.StandardOutput.ReadToEnd()
  $stderr = $proc.StandardError.ReadToEnd()
  $proc.WaitForExit()

  if ($stdout) { $stdout | Tee-Object -FilePath $logPath -Append | Out-Null }
  if ($stderr) { "ERR: $stderr" | Tee-Object -FilePath $logPath -Append | Out-Null }

$had429 = ($stdout -match '429 rate-limit') -or ($stderr -match '429') -or ($stdout -match 'Retry-After')
  if ($proc.ExitCode -ne 0) {
    Write-Warning "Shim exited with code $($proc.ExitCode). Check the log: $logPath"
    $sleepMs = [Math]::Max($ThrottleMs + 1000, 3000)
    Start-Sleep -Milliseconds $sleepMs
  } else {
    # If we saw signs of throttling, bump throttle for the next slice by 25% (cap 5000ms)
    if ($had429) {
      $ThrottleMs = [Math]::Min([int]([double]$ThrottleMs * 1.25), 5000)
      "INFO: Detected throttling; increasing ThrottleMs to $ThrottleMs ms" | Tee-Object -FilePath $logPath -Append | Out-Null
    }
    Start-Sleep -Milliseconds $ThrottleMs
  }

"Finished: $(Get-Date)" | Tee-Object -FilePath $logPath -Append | Out-Null
Write-Host "Harvest complete. Log: $logPath" -ForegroundColor Green
