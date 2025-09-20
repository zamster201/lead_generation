from __future__ import annotations
import os, sys, csv, json, sqlite3, argparse, datetime, configparser
from pathlib import Path
from typing import Dict, Any, List

from scoring import fit_score as compute_fit, risk_score as compute_risk
from sam_client import request_sam, map_sam_item_to_lead
from change_detect import compute_rev_hash, upsert_opportunity

DATE_FMT_OUT = "%Y-%m-%d"

# -------------------- helpers --------------------

def _parse_cfg(cfg_path: str | None) -> Dict[str, Any]:
    cfg = {
        "filters": {
            "naics_allow": set(),
            "set_aside_allow": set(),
            "min_est_value": 0,
            "agencies_priority": set(),
            "vehicles_priority": set(),
            "keywords": []
        },
        "scoring": {"due_soon_days": 14},
        "history_agencies": []
    }
    if not cfg_path:
        return cfg
    cp = configparser.ConfigParser()
    cp.read(cfg_path, encoding="utf-8")
    f = cp["filters"]
    s = cp["scoring"]
    cfg["filters"]["naics_allow"] = set(x.strip() for x in f.get("naics_allow","").split(",") if x.strip())
    cfg["filters"]["set_aside_allow"] = set(x.strip().lower() for x in f.get("set_aside_allow","").split(",") if x.strip())
    cfg["filters"]["min_est_value"] = int(f.get("min_est_value","0") or 0)
    cfg["filters"]["agencies_priority"] = set(x.strip() for x in f.get("agencies_priority","").split(",") if x.strip())
    cfg["filters"]["vehicles_priority"] = set(x.strip() for x in f.get("vehicles_priority","").split(",") if x.strip())
    cfg["filters"]["keywords"] = [x.strip() for x in f.get("keywords","").split(",") if x.strip()]
    cfg["scoring"]["due_soon_days"] = int(s.get("due_soon_days","14") or 14)
    return cfg

def _ensure_schema(conn: sqlite3.Connection, schema_sql_path: str | None):
    if not schema_sql_path:
        return
    sql = Path(schema_sql_path).read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()

def _iso(date_str: str | None) -> str | None:
    if not date_str:
        return None
    s = str(date_str).strip()
    # handle ISO-8601 with T/Z
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.datetime.strptime(s, fmt).strftime(DATE_FMT_OUT)
        except Exception:
            pass
    return None

def _days_to_due(iso_due: str | None) -> int:
    if not iso_due:
        return 9999
    try:
        due = datetime.datetime.strptime(iso_due, DATE_FMT_OUT).date()
        return (due - datetime.date.today()).days
    except Exception:
        return 9999

def _format_mmddyyyy(iso_date: str) -> str:
    dt = datetime.datetime.strptime(iso_date, DATE_FMT_OUT)
    return dt.strftime("%m/%d/%Y")

def _sam_params(args: argparse.Namespace) -> Dict[str, Any]:
    pf = _format_mmddyyyy(args.from_date)
    pt = _format_mmddyyyy(args.to_date)
    return {"api_key": args.sam_api_key, "q": args.query, "from": pf, "to": pt, "limit": args.limit}

def _match_keywords(text: str, kws: List[str]) -> List[str]:
    if not text:
        return []
    t = text.lower()
    return [k for k in kws if k.lower() in t]

def _export_artifacts(leads, export_dir: Path, base_name: str, want_csv: bool, want_ndjson: bool, overwrite: bool):
    export_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = export_dir / f"{base_name}_{stamp}.csv"
    ndjson_path = export_dir / f"{base_name}_{stamp}.ndjson"
    if want_csv:
        if csv_path.exists() and not overwrite:
            raise RuntimeError(f"CSV exists: {csv_path}")
        if leads:
            keys = sorted({k for d in leads for k in d.keys()})
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                for d in leads:
                    w.writerow(d)
    if want_ndjson:
        if ndjson_path.exists() and not overwrite:
            raise RuntimeError(f"NDJSON exists: {ndjson_path}")
        with ndjson_path.open("w", encoding="utf-8") as f:
            for d in leads:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")

# -------------------- main --------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["prod","dev"], default="prod",
                    help="Which API key env var to use (prod=SAM_API_KEY_1, dev=SAM_API_KEY_2)")
    ap.add_argument("--sam-api-key", dest="sam_api_key", default="",
                    help="Explicit SAM API key (overrides profile)")
    ap.add_argument("--from", dest="from_date", default=(datetime.date.today()-datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
                    help="From date (YYYY-MM-DD, default=yesterday)")
    ap.add_argument("--to", dest="to_date", default=datetime.date.today().strftime("%Y-%m-%d"),
                    help="To date (YYYY-MM-DD, default=today)")
    ap.add_argument("--limit", type=int, default=250)
    ap.add_argument("--query", default="cybersecurity OR analytics OR AI OR integration")
    ap.add_argument("--db", default=r"C:\CTS\Lead_Generation\data\cts_opportunities.db")
    ap.add_argument("--filters-config", dest="filters_config", default=r"C:\CTS\Lead_Generation\configs\leadgen.cfg")
    ap.add_argument("--schema-sql", dest="schema_sql", default=r"C:\CTS\Lead_Generation\src\opportunities_schema.sql")
    ap.add_argument("--export-dir", default=r"E:\LeadGen\Logs")
    ap.add_argument("--overwrite-exports", dest="overwrite", type=str, default="true")
    ap.add_argument("--csv", action="store_true")
    ap.add_argument("--ndjson", action="store_true")
    args = ap.parse_args()

    # default: always export csv+ndjson unless explicitly disabled
    if not args.csv and not args.ndjson:
        args.csv = args.ndjson = True

    # resolve API key
    if not args.sam_api_key:
        env_name = "SAM_API_KEY_1" if args.profile == "prod" else "SAM_API_KEY_2"
        args.sam_api_key = os.environ.get(env_name, "")
        if not args.sam_api_key:
            print(f"ERROR: Env var {env_name} not found or empty", file=sys.stderr)
            sys.exit(2)

    # normalize dates
    args.from_date = _iso(args.from_date) or datetime.date.today().strftime(DATE_FMT_OUT)
    args.to_date   = _iso(args.to_date) or datetime.date.today().strftime(DATE_FMT_OUT)
    overwrite = str(args.overwrite).lower() in {"1","true","yes","y"}
    cfg = _parse_cfg(args.filters_config) if args.filters_config else _parse_cfg(None)

    # DB setup
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db)
    if args.schema_sql:
        _ensure_schema(conn, args.schema_sql)

    leads: List[Dict[str, Any]] = []

    if args.source == "sam" or True:  # only source supported
        params = _sam_params(args)
        for raw in request_sam(params):
            lead = map_sam_item_to_lead(raw)
            if not lead.get("opportunity_id"):
                continue
            lead["posted_date"] = _iso(lead.get("posted_date"))
            lead["due_date"] = _iso(lead.get("due_date"))
            lead["days_to_due"] = _days_to_due(lead["due_date"])
            text = (lead.get("title","") or "") + " " + (lead.get("summary","") or "")
            hits = _match_keywords(text, cfg["filters"]["keywords"])
            lead["keywords"] = ";".join(hits)
            lead["fit_score"] = compute_fit(lead, cfg)
            lead["risk_score"] = compute_risk(lead, cfg)
            lead["rev_hash"] = compute_rev_hash(
                lead.get("title",""), lead.get("due_date",""), int(lead.get("attachments_count") or 0)
            )
            upsert_opportunity(conn, lead)
            leads.append(lead)

    if args.export_dir and (args.csv or args.ndjson):
        export_dir = Path(args.export_dir) / "Opportunities" / datetime.date.today().strftime("%Y") / datetime.date.today().strftime("%m")
        _export_artifacts(leads, export_dir, "sam_opportunities", args.csv, args.ndjson, overwrite)

    print(json.dumps({
        "source": "sam",
        "from": args.from_date,
        "to": args.to_date,
        "count": len(leads),
        "export_dir": args.export_dir,
        "csv": bool(args.csv),
        "ndjson": bool(args.ndjson)
    }))

if __name__ == "__main__":
    main()
