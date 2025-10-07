@{
  # Shim args
  SamApiKey    = $env:SAM_API_KEY           # or put the literal key here
  Query        = 'Kove software defined memory virtualization storage performance'
  From         = '2025-01-01'
  To           = '2025-08-26'
  Limit        = 50
  DbPath       = 'C:\CTS\Lead_Generation\leads.db'
  ExportDir    = 'C:\CTS\Lead_Generation\exports'
  SewpFile     = 'C:\CTS\Lead_Generation\data\sewp_export.xlsx'  # '' if not used
  NitaacFile   = 'C:\CTS\Lead_Generation\data\nitaac_export.csv' # '' if not used
  NoSam        = $false

  # Rate-limit hygiene (passed through to shim/harvester)
  ThrottleMs   = 1200
  MaxRetries   = 6
  Verbose      = $true
}
