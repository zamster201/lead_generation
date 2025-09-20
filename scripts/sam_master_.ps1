python C:\CTS\Lead_Generation\src\cts_opps_pipeline.py `
  --profile prod `
  --from 2025-01-01 --to 2025-03-31 `
  --limit 200 `
  --require-keyword-match `
  --db C:\CTS\Lead_Generation\data\cts_opportunities.db `
  --filters-config C:\CTS\Lead_Generation\configs\leadgen.cfg `
  --schema-sql C:\CTS\Lead_Generation\src\opportunities_schema.sql `
  --export-dir E:\LeadGen\Logs --overwrite-exports true --csv --ndjson
