CT Lead Generation — Starter Pack (v0.2)

Folders:
- configs/leadgen.cfg           — filters + scoring knobs
- src/opportunities_schema.sql  — SQLite schema for opportunities
- src/scoring.py                — fit_score / risk_score heuristics
- src/sam_client.py             — request_sam() + map_sam_item_to_lead()
- src/change_detect.py          — revision hash + UPSERT helper
- src/write_triage.py           — emits Outputs/Daily_Triage_YYYY-MM-DD.md
- scripts/daily_incremental.ps1 — daily pipeline + triage

Quick wire-up in cts_opps_pipeline.py:
- load cfg → call request_sam → map → compute days_to_due → score → compute_rev_hash → upsert.
- keep status_stage sticky for human edits.

Date: 2025-09-10
