python C:\CTS\Lead_Generation\src\cts_opps_pipeline.py `
  --profile prod `
  --from 2025-01-01 --to 2025-01-15 --limit 25 `
  --db $env:dbPath `
  --filters-config C:\CTS\Lead_Generation\configs\leadgen.cfg `
  --export-dir E:\LeadGen\Logs --csv --ndjson `
  --fetch-summaries
