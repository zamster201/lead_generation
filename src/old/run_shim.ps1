param(
  [Parameter(Mandatory=$true)]
  [string]$ProfilePath  # e.g. C:\CTS\Lead_Generation\configs\kove-dev.psd1
)

if (-not (Test-Path $ProfilePath)) { throw "Profile not found: $ProfilePath" }
$cfg = Import-PowerShellDataFile -Path $ProfilePath

# Optional: source shared env (keeps API keys out of psd1 files)
$sharedEnv = Join-Path (Split-Path $ProfilePath -Parent) 'shared.env.ps1'
if (Test-Path $sharedEnv) { . $sharedEnv }

$shim = "C:\CTS\Lead_Generation\src\cts_shim_multi_sources.py"
if (-not (Test-Path $shim)) { throw "Shim not found: $shim" }

# Build argument list from profile (only include non-empty values)
$argv = @("$shim")
if ($cfg.SamApiKey)    { $argv += @("--sam-api-key", "`"$($cfg.SamApiKey)`"") } else { $argv += "--no-sam" }
if ($cfg.Query)        { $argv += @("--query", "`"$($cfg.Query)`"") }
if ($cfg.From)         { $argv += @("--from",  $cfg.From) }
if ($cfg.To)           { $argv += @("--to",    $cfg.To) }
if ($cfg.Limit)        { $argv += @("--limit", $cfg.Limit) }
if ($cfg.SewpFile)     { $argv += @("--sewp-file", "`"$($cfg.SewpFile)`"") }
if ($cfg.NitaacFile)   { $argv += @("--nitaac-file", "`"$($cfg.NitaacFile)`"") }
if ($cfg.DbPath)       { $argv += @("--db-path", "`"$($cfg.DbPath)`"") }
if ($cfg.ExportDir)    { $argv += @("--export-dir", "`"$($cfg.ExportDir)`"") }
if ($cfg.ThrottleMs)   { $argv += @("--throttle-ms", $cfg.ThrottleMs) }
if ($cfg.MaxRetries)   { $argv += @("--max-retries", $cfg.MaxRetries) }
if ($cfg.Verbose)      { $argv += "--verbose" }

# Logging
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logDir = "C:\CTS\Lead_Generation\logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$log = Join-Path $logDir "shim_$stamp.log"

Write-Host "Running shim with profile: $ProfilePath"
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "python"
$psi.Arguments = ($argv -join " ")
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError  = $true
$psi.UseShellExecute = $false
$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
[void]$proc.Start()
$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()
$stdout | Out-File -FilePath $log -Encoding utf8
if ($stderr) { "ERR: $stderr" | Add-Content -Path $log }

Write-Host "Done. Log: $log"
exit $proc.ExitCode
