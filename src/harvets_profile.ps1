param(
  [Parameter(Mandatory=$true)]
  [string]$ProfilePath
)

$cfg = Import-PowerShellDataFile -Path $ProfilePath
$harvester = "C:\CTS\Lead_Generation\src\cts_harvest_sam.ps1"

# Fallbacks (if missing in profile)
$cfg.ThrottleMs = $cfg.ThrottleMs ?? 1500
$cfg.MaxRetries = $cfg.MaxRetries ?? 6

# Build call
$cmd = @(
  $harvester,
  "-Query",  "`"$($cfg.Query)`"",
  "-From",   $cfg.From,
  "-To",     $cfg.To,
  "-Limit",  $cfg.Limit,
  "-ThrottleMs", $cfg.ThrottleMs,
  "-MaxRetries", $cfg.MaxRetries,
  "-DbPath", "`"$($cfg.DbPath)`"",
  "-ExportDir", "`"$($cfg.ExportDir)`""
)
if ($cfg.SamApiKey) { $cmd += @("-SamApiKey", "`"$($cfg.SamApiKey)`"") } else { $cmd += "-NoSam" }

Write-Host "Harvesting with profile: $ProfilePath"
& pwsh @cmd
