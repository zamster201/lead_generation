param(
  [string[]] $Paths = @(
    "C:\CTS\Lead_Generation\exports",
    "C:\CTS\Utilities\pdf_index_search\exports",
    "C:\CTS\RFP_Hunter\exports"
  ),
  [string[]] $FilePatterns = @("*.json","*.csv","*.md","*.ndjson"),
  [switch]   $PurgeSubdirs,
  [bool]     $DryRun = $true
)

Write-Host "[INFO] DryRun=$DryRun  PurgeSubdirs=$($PurgeSubdirs.IsPresent)"
Write-Host "[INFO] Scanning paths:"; $Paths | ForEach-Object { Write-Host "  - $_" }
Write-Host "[INFO] FilePatterns: $($FilePatterns -join ', ')"

function Remove-ItemSafe {
  param([string]$Target)
  if ($DryRun) { Write-Host "[DRY-RUN] DEL $Target"; return }
  try {
    Remove-Item -LiteralPath $Target -Force -ErrorAction Stop
    Write-Host "[OK] Deleted $Target"
  } catch {
    Write-Warning ("Failed to delete {0}: {1}" -f $Target, $_.Exception.Message)
  }
}

foreach ($p in $Paths) {
  if (-not (Test-Path $p)) { Write-Warning "Skip (missing): $p"; continue }
  Write-Host "`n==> Scanning $p"

  foreach ($pat in $FilePatterns) {
    Get-ChildItem -LiteralPath $p -Recurse:$PurgeSubdirs.IsPresent -File -Filter $pat -ErrorAction SilentlyContinue |
      ForEach-Object { Remove-ItemSafe -Target $_.FullName }
  }

  if ($PurgeSubdirs) {
    # Remove now-empty directories (deepest first)
    Get-ChildItem -LiteralPath $p -Recurse -Directory |
      Sort-Object FullName -Descending |
      ForEach-Object {
        if (-not (Get-ChildItem -LiteralPath $_.FullName -Recurse -Force)) {
          Remove-ItemSafe -Target $_.FullName
        }
      }
  }
}

Write-Host "`nDone. Tip: run with -DryRun:`$false for actual deletion."
