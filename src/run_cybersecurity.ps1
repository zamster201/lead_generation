# Run SAM.gov ingest for cybersecurity opportunities
python .\cts_shim_multi_sources.py `
  --sam-api-key "$env:SAM_API_KEY" `
  --query "cybersecurity" `
  --from 2025-08-01 --to 2025-08-15 `
  --limit 20 `
  --verbose `
  --throttle-ms 5000 --max-retries 8
