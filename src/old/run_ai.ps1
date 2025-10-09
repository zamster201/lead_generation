# Run SAM.gov ingest for AI opportunities
python .\cts_shim_multi_sources.py `
  --sam-api-key "$env:SAM_API_KEY" `
  --query "AI" `
  --from 2025-08-01 --to 2025-08-31 `
  --limit 200 `
  --verbose `
  --throttle-ms 5000 --max-retries 8
