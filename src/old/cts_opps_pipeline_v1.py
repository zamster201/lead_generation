#!/usr/bin/env python3
"""
CTS Opportunity Pipeline

One script to ingest → normalize → upsert into SQLite → export artifacts.

Usage (examples):
  python cts_opps_pipeline.py \
    --source sam \
    --from 2025-08-01 --to 2025-08-31 \
    --limit 200 \
    --db C:\\CTS\\Lead_Generation\\data\\cts_opportunities.db \
    --export-dir C:\\CTS\\Lead_Generation\\exports \
    --overwrite-exports true \
    --csv --ndjson

Notes:
- Uses opportunity_id as the upsert key.
- Overwrites per-lead Markdown/JSON by default (toggle with --overwrite-exports).
- Exports batch CSV/NDJSON if flags passed.
- Minimal dependencies (stdlib only).

TODO hooks to wire real ingestors for SAM/GovWin/FPDS.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional

# -----------------------------
# Canonical Lead Model
# -----------------------------
@dataclass
class Lead:
    title: str
    source_url: str
    opportunity_id: str
    agency: str = ""
    vehicle: str = ""
    posted_date: str = ""      # YYYY-MM-DD
    due_date: str = ""         # YYYY-MM-DD
    status_stage: str = "new"   # new/screen/qual/bid/no-bid/submitted/won/lost
    est_value: Optional[float] = None
    contract_type: str = ""
    naics: str = ""
    set_aside: str = ""
    keywords: List[str] = None
    fit_score: Optional[float] = None
    risk_score: Optional[float] = None
    requirements_summary: str = ""
    compliance_checklist: List[str] = None
    contacts: List[Dict[str, str]] = None
    partners: List[Dict[str, str]] = None
    notes: str = ""
    origin: str = "cts_shim"
    generated_by: str = "cts_opps_pipeline.py"
    generated_on: str = ""       # ISO timestamp
    reviewed: bool = False

    def to_row(self) -> Dict[str, Any]:
        d = asdict(self)
        # JSON-encode list/dict fields for SQLite text columns
        for k in ["keywords", "compliance_checklist", "contacts", "partners"]:
            d[k] = json.dumps(d[k] or [])
        return d


# -----------------------------
# Utilities
# -----------------------------
SLUG_RX = re.compile(r"[^a-z0-9]+")

def iso_today() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def yyyymm(d: str) -> str:
    try:
        return dt.datetime.strptime(d, "%Y-%m-%d").strftime("%Y/%m")
    except Exception:
        # fallback to current
        now = dt.datetime.utcnow()
        return now.strftime("%Y/%m")

def make_slug(text: str) -> str:
    s = text.lower().strip()
    s = SLUG_RX.sub("-", s).strip("-")
    return s[:90]

# -----------------------------
# Filesystem Artifacts
# -----------------------------
MD_HEADER = (
    "created: {created}\n"
    "edited: {edited}\n"
    "origin: {origin}\n"
    "source: {source}\n"
    "wf_status: unfiled\n"
    "tags: [\"ClearTrend\",\"Opportunity\",\"{agency}\",\"{naics}\",\"{vehicle}\"]\n\n"
)

MD_BODY = (
    "# {opportunity_id} — {title}\n\n"
    "- Source: {source_url}\n"
    "- Agency: {agency} | Vehicle: {vehicle}\n"
    "- Posted: {posted_date} | Due: {due_date}\n"
    "- Status: {status_stage}\n"
    "- Value (est.): {est_value} | Contract: {contract_type}\n"
    "- NAICS: {naics} | Set-aside: {set_aside}\n"
    "- Fit score: {fit_score} | Risk score: {risk_score}\n\n"
    "## Requirements Summary\n{requirements_summary}\n\n"
    "## Compliance Checklist\n{checklist}\n\n"
    "## Contacts\n{contacts}\n\n"
    "## Partners\n{partners}\n\n"
    "## Notes\n{notes}\n"
)

def render_md(lead: Lead) -> str:
    created = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    edited = created
    checklist = "\n".join([f"- [ ] {item}" for item in (lead.compliance_checklist or [])]) or "-"
    contacts = "\n".join([f"- {c.get('name','')} — {c.get('role','')} — {c.get('email','')}" for c in (lead.contacts or [])]) or "-"
    partners = "\n".join([f"- {p.get('name','')} — {p.get('role','')} — {p.get('notes','')}" for p in (lead.partners or [])]) or "-"

    header = MD_HEADER.format(
        created=created,
        edited=edited,
        origin=lead.origin,
        source="sam.gov" if "sam" in (lead.source_url or "") else "external",
        agency=lead.agency or "",
        naics=lead.naics or "",
        vehicle=lead.vehicle or "",
    )
    body = MD_BODY.format(
        opportunity_id=lead.opportunity_id,
        title=lead.title,
        source_url=lead.source_url,
        agency=lead.agency,
        vehicle=lead.vehicle,
        posted_date=lead.posted_date,
        due_date=lead.due_date,
        status_stage=lead.status_stage,
        est_value=lead.est_value if lead.est_value is not None else "",
        contract_type=lead.contract_type,
        naics=lead.naics,
        set_aside=lead.set_aside,
        fit_score=lead.fit_score if lead.fit_score is not None else "",
        risk_score=lead.risk_score if lead.risk_score is not None else "",
        requirements_summary=lead.requirements_summary or "",
        checklist=checklist,
        contacts=contacts,
        partners=partners,
        notes=lead.notes or "",
    )
    return header + body


def write_artifacts(lead: Lead, export_dir: Path, overwrite: bool) -> Dict[str, Path]:
    folder = export_dir / "Opportunities" / yyyymm(lead.posted_date or lead.due_date)
    folder.mkdir(parents=True, exist_ok=True)
    filename_base = f"{lead.opportunity_id} — {make_slug(lead.title)}"

    md_path = folder / f"{filename_base}.md"
    json_path = folder / f"{filename_base}.json"

    if not overwrite and md_path.exists():
        pass
    else:
        md_path.write_text(render_md(lead), encoding="utf-8")

    if not overwrite and json_path.exists():
        pass
    else:
        # Write canonical JSON (list/dict fields remain as objects here)
        j = asdict(lead)
        j["generated_on"] = iso_today()
        json_path.write_text(json.dumps(j, indent=2, ensure_ascii=False), encoding="utf-8")

    return {"md": md_path, "json": json_path}

# -----------------------------
# SQLite
# -----------------------------
DDL_MIN = """
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY,
  opportunity_id TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  source_url TEXT,
  agency TEXT,
  vehicle TEXT,
  posted_date TEXT,
  due_date TEXT,
  status_stage TEXT,
  est_value NUMERIC,
  contract_type TEXT,
  naics TEXT,
  set_aside TEXT,
  keywords TEXT,
  fit_score REAL,
  risk_score REAL,
  requirements_summary TEXT,
  compliance_checklist TEXT,
  contacts TEXT,
  partners TEXT,
  notes TEXT,
  origin TEXT,
  generated_by TEXT,
  generated_on TEXT,
  reviewed INTEGER,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_leads_due_date ON leads(due_date);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status_stage);
CREATE INDEX IF NOT EXISTS idx_leads_agency ON leads(agency);
CREATE INDEX IF NOT EXISTS idx_leads_naics ON leads(naics);
"""

UPSERT_SQL = """
INSERT INTO leads (
  opportunity_id,title,source_url,agency,vehicle,posted_date,due_date,status_stage,
  est_value,contract_type,naics,set_aside,keywords,fit_score,risk_score,
  requirements_summary,compliance_checklist,contacts,partners,notes,
  origin,generated_by,generated_on,reviewed,updated_at
) VALUES (
  :opportunity_id,:title,:source_url,:agency,:vehicle,:posted_date,:due_date,:status_stage,
  :est_value,:contract_type,:naics,:set_aside,:keywords,:fit_score,:risk_score,
  :requirements_summary,:compliance_checklist,:contacts,:partners,:notes,
  :origin,:generated_by,:generated_on,:reviewed,datetime('now')
)
ON CONFLICT(opportunity_id) DO UPDATE SET
  title=excluded.title,
  source_url=excluded.source_url,
  agency=excluded.agency,
  vehicle=excluded.vehicle,
  posted_date=excluded.posted_date,
  due_date=excluded.due_date,
  status_stage=excluded.status_stage,
  est_value=excluded.est_value,
  contract_type=excluded.contract_type,
  naics=excluded.naics,
  set_aside=excluded.set_aside,
  keywords=excluded.keywords,
  fit_score=excluded.fit_score,
  risk_score=excluded.risk_score,
  requirements_summary=excluded.requirements_summary,
  compliance_checklist=excluded.compliance_checklist,
  contacts=excluded.contacts,
  partners=excluded.partners,
  notes=excluded.notes,
  origin=excluded.origin,
  generated_by=excluded.generated_by,
  generated_on=excluded.generated_on,
  reviewed=excluded.reviewed,
  updated_at=datetime('now');
"""


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL_MIN)


def upsert_leads(conn: sqlite3.Connection, leads: Iterable[Lead]) -> Dict[str, int]:
    added = 0
    updated = 0
    cur = conn.cursor()
    for lead in leads:
        d = lead.to_row()
        # detect add vs update by probing
        cur.execute("SELECT 1 FROM leads WHERE opportunity_id=?", (lead.opportunity_id,))
        existed = cur.fetchone() is not None
        cur.execute(UPSERT_SQL, d)
        if existed:
            updated += 1
        else:
            added += 1
    conn.commit()
    return {"added": added, "updated": updated}

# -----------------------------
# Ingest Stubs
# -----------------------------

def ingest_mock(limit: int) -> List[Lead]:
    base = dt.date.today()
    items: List[Lead] = []
    for i in range(1, max(1, limit) + 1):
        oid = f"MOCK-{base.strftime('%Y%m%d')}-{i:04d}"
        items.append(Lead(
            title=f"Mock Opportunity {i}",
            source_url="https://sam.gov/opportunity/mock",
            opportunity_id=oid,
            agency="GSA",
            vehicle="SEWP",
            posted_date=(base - dt.timedelta(days=5)).strftime("%Y-%m-%d"),
            due_date=(base + dt.timedelta(days=15)).strftime("%Y-%m-%d"),
            status_stage="new",
            est_value=100000.0 + i,
            contract_type="FFP",
            naics="541512",
            set_aside="SB",
            keywords=["cybersecurity","SEWP","cloud"],
            fit_score=0.7,
            risk_score=0.3,
            requirements_summary="High-level requirements...",
            compliance_checklist=["SAM active","NAICS eligible"],
            contacts=[{"name":"CO Smith","email":"co.smith@gsa.gov","role":"CO"}],
            partners=[{"name":"Acme","role":"Prime","notes":"Past perf."}],
            notes="",
            generated_on=iso_today(),
        ))
    return items


def ingest_sam(date_from: str, date_to: str, limit: int, *,
               api_key: Optional[str] = None,
               query: str = "",
               throttle_ms: int = 1500,
               max_retries: int = 5) -> List[Lead]:
    """SAM.gov ingestor (stub wiring).

    Notes:
      - This function is structured for easy drop-in of real HTTP calls.
      - Until wired, it returns mock leads tagged as SAM to validate the pipeline.
      - Respect rate limits when you implement: personal vs system account quotas.
    """
    if not api_key:
        print("[WARN] --sam-api-key missing. Returning mock leads for pipeline validation.")
        leads = ingest_mock(limit)
        for l in leads:
            l.source_url = "https://sam.gov/opp/placeholder"
        return leads

    # TODO: implement _request_sam(...) with pagination, throttling, and backoff
    # results = _request_sam(api_key=api_key, q=query, posted_from=date_from, posted_to=date_to,
    #                        limit=limit, throttle_ms=throttle_ms, max_retries=max_retries)
    # leads: List[Lead] = [_map_sam_item_to_lead(item) for item in results]

    # Temporary placeholder to keep behavior deterministic during wiring
    leads = ingest_mock(min(limit, 25))
    for l in leads:
        l.source_url = "https://sam.gov/opp/placeholder"
        l.title = f"[SAM] {l.title}"
    return leads

# -----------------------------
# Batch Exports
# -----------------------------

def export_csv(leads: List[Lead], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "opportunity_id","title","agency","vehicle","posted_date","due_date","status_stage",
        "est_value","contract_type","naics","set_aside","fit_score","risk_score","source_url"
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for l in leads:
            row = {k: getattr(l, k) for k in fields}
            writer.writerow(row)


def export_ndjson(leads: List[Lead], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for l in leads:
            f.write(json.dumps(asdict(l), ensure_ascii=False) + "\n")

# -----------------------------
# Main
# -----------------------------

def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="CTS Opportunity Pipeline")
    p.add_argument("--source", choices=["sam","govwin","fpds","mock"], required=True)
    p.add_argument("--from", dest="date_from", help="YYYY-MM-DD")
    p.add_argument("--to", dest="date_to", help="YYYY-MM-DD")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--db", required=True)
    p.add_argument("--export-dir", required=True)
    p.add_argument("--overwrite-exports", type=str, default="true", help="true|false")
    p.add_argument("--csv", action="store_true")
    p.add_argument("--ndjson", action="store_true")
    # SAM.gov specific (stub-ready)
    p.add_argument("--sam-api-key", dest="sam_api_key")
    p.add_argument("--query", dest="query", default="")
    p.add_argument("--throttle-ms", dest="throttle_ms", type=int, default=1500)
    p.add_argument("--max-retries", dest="max_retries", type=int, default=5)
    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    overwrite = str(args.overwrite_exports).lower() in ("1","true","yes","y")

    db_path = Path(args.db)
    export_dir = Path(args.export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    # Ingest
    if args.source == "mock":
        leads = ingest_mock(args.limit)
    elif args.source == "sam":
        leads = ingest_sam(
            args.date_from or "",
            args.date_to or "",
            args.limit,
            api_key=args.sam_api_key,
            query=args.query,
            throttle_ms=args.throttle_ms,
            max_retries=args.max_retries,
        )
    else:
        print(f"[WARN] Source '{args.source}' not wired yet — using mock leads for pipeline test.")
        leads = ingest_mock(args.limit)

    # Normalize / enrich default fields
    for l in leads:
        l.generated_by = "cts_opps_pipeline.py"
        if not l.generated_on:
            l.generated_on = iso_today()
        # ensure list fields not None
        l.keywords = l.keywords or []
        l.compliance_checklist = l.compliance_checklist or []
        l.contacts = l.contacts or []
        l.partners = l.partners or []

    # SQLite upsert
    conn = sqlite3.connect(str(db_path))
    try:
        ensure_schema(conn)
        result = upsert_leads(conn, leads)
    finally:
        conn.close()

    # Per-lead artifacts
    written = 0
    for l in leads:
        write_artifacts(l, export_dir=export_dir, overwrite=overwrite)
        written += 1

    # Batch exports
    if args.csv:
        export_csv(leads, export_dir / "opportunities.csv")
    if args.ndjson:
        export_ndjson(leads, export_dir / "opportunities.ndjson")

    # Summary
    print(
        json.dumps({
            "source": args.source,
            "ingested": len(leads),
            "db_added": result.get("added", 0),
            "db_updated": result.get("updated", 0),
            "artifacts_written": written,
            "export_dir": str(export_dir),
        }, indent=2)
    )

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
# -----------------------------
# SAM.gov Helpers (stubs to wire later)
# -----------------------------

def _request_sam(*, api_key: str, q: str, posted_from: str, posted_to: str,
                 limit: int, throttle_ms: int, max_retries: int) -> List[Dict[str, Any]]:
    """Placeholder for the real HTTP/pagination logic.
    Implement with requests/httpx; apply throttling and exponential backoff on 429.
    Return a list of raw SAM.gov items to be mapped via _map_sam_item_to_lead().
    """
    raise NotImplementedError("Wire SAM.gov HTTP client here.")


def _map_sam_item_to_lead(item: Dict[str, Any]) -> Lead:
    """Map a SAM.gov item (JSON) into the canonical Lead model.
    Fill: opportunity_id, title, agency, vehicle (if detectable), dates, etc.
    """
    # Example placeholder mapping — adjust once real fields are known
    return Lead(
        title=item.get("title", ""),
        source_url=item.get("url", ""),
        opportunity_id=item.get("noticeId") or item.get("solicitationNumber") or "",
        agency=item.get("agency",""),
        posted_date=item.get("publishDate",""),
        due_date=item.get("responseDueDate",""),
    )


# -----------------------------
# Smoke Test (optional separate file if desired)
# -----------------------------
# Suggested separate file name: smoke_test.py
# from cts_opps_pipeline import Lead, ensure_schema, upsert_leads
# def run():
#     import sqlite3, tempfile
#     import pathlib
#     tmpdb = pathlib.Path(tempfile.gettempdir())/"cts_smoke.db"
#     conn = sqlite3.connect(tmpdb)
#     ensure_schema(conn)
#     res = upsert_leads(conn, [Lead(title="Smoke", source_url="", opportunity_id="SMOKE-1")])
#     print("SMOKE:", res)
# if __name__ == "__main__":
#     run()

