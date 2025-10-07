python C:\CTS\Lead_Generation\src\cts_opps_pipeline.py `
  --sam-api-key "$env:SAM_API_KEY_1" `
  --from 2025-01-01 --to 2025-03-31 `
  --limit 50 `
  --db C:\CTS\Lead_Generation\data\cts_opportunities.db `
  --filters-config C:\CTS\Lead_Generation\configs\leadgen.cfg `
  --schema-sql C:\CTS\Lead_Generation\src\opportunities_schema.sql `
  --export-dir E:\LeadGen\Logs `
  --csv --ndjson `
  --require-keyword-match
