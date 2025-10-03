from __future__ import annotations
import os, sys, csv, json, sqlite3, argparse, datetime, configparser, re
from pathlib import Path
from typing import Dict, Any, List
import re
import string
from collections import defaultdict
from write_runlog import write_runlog

from scoring import fit_score as compute_fit, risk_score as compute_risk
from sam_client import request_sam
from change_detect import compute_rev_hash, upsert_opportunity
from fetch_summaries import fetch_summary_text

DATE_FMT_OUT = "%Y-%m-%d"

# -------------------- helpers --------------------

def _parse_cfg(cfg_path: str):
    cp = configparser.ConfigParser(strict=False, delimiters=("="))
    cp.optionxform = str  # preserve case
    cp.read(cfg_path, encoding="utf-8")

    cfg = {"filters": {}, "scoring": {}, "portfolios": {}}

    for section in cp.sections():
        if section.startswith("portfolio_"):
            # Flatten into a list of keywords
            kws = []
            for _, value in cp.items(section):
                kws.extend([v.strip() for v in value.split(",") if v.strip()])
            cfg["portfolios"][section] = kws
        elif section == "filters":
            cfg["filters"].update(cp.items(section))
        elif section == "scoring":
            cfg["scoring"].update(cp.items(section))

    return cfg

# inside cts_opps_pipeline.py (near the top, after imports)

def _first(d: dict, keys: list):
    """Return the first non-empty value from dict d for the provided keys."""
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return None

def map_sam_item_to_lead(raw: dict) -> dict:
    """Normalize a SAM.gov record into CTS opportunity schema."""
    opp_id = _first(raw, ["id", "noticeId", "solicitationNumber"])
    title  = _first(raw, ["title", "noticeTitle", "subject"])
    agency = _first(raw, ["agency", "agencyName", "organizationName", "department"])
    due    = _first(raw, ["responseDate", "dueDate", "offersDueDate"])
    posted = _first(raw, ["postedDate", "publishDate", "datePosted"])
    estval = _first(raw, ["estimatedValue", "value", "awardCeiling"])
    naics  = _first(raw, ["naics", "naicsCode", "primaryNaics"])
    setas  = _first(raw, ["setAside", "setAsideCode", "typeOfSetAside"])
    desc   = _first(raw, ["description", "summary", "synopsis"])
    url    = _first(raw, ["uiLink", "link", "detailUrl"])

    return {
        "source": "sam",
        "opportunity_id": opp_id or "",
        "title": title or "",
        "agency": agency or "",
        "due_date": due or "",
        "posted_date": posted or "",
        "est_value": estval or 0,
        "naics": naics or "",
        "set_aside": setas or "",
        "summary": desc or "",
        "url": url or "",
    }


def _sync_portfolios_to_db(conn: sqlite3.Connection, portfolios: Dict[str, List[str]]):
    conn.execute("DELETE FROM portfolios")  # wipe and reload
    for pname, kws in portfolios.items():
        conn.execute(
            "INSERT INTO portfolios (portfolio_id, name, keywords) VALUES (?,?,?)",
            (pname, pname.capitalize(), ";".join(kws))
        )
    conn.commit()

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

# --- keyword/portfolio matching ---
SHORT_KEYWORD_ALLOWLIST = {"ai", "it", "ml", "ehr"}

def _normalize_text(txt: str) -> str:
    if not txt:
        return ""
    # lowercase, replace punctuation with spaces
    table = str.maketrans(string.punctuation, " " * len(string.punctuation))
    return re.sub(r"\s+", " ", txt.translate(table).lower()).strip()

def _expand_keyword(kw: str):
    """
    Expand tricky keywords like 'AI/ML' -> ['ai', 'ml', 'ai ml']
    and 'zero-trust' -> ['zero trust'].
    """
    parts = re.split(r"[/\-]", kw.lower())
    expanded = [kw.lower()]
    if len(parts) > 1:
        expanded.extend(parts)
        expanded.append(" ".join(parts))
    return expanded

def _match_portfolios_and_hits(text: str, portfolios: dict):
    norm_text = _normalize_text(text)
    pmatches = set()
    actual_hits = defaultdict(list)
    universe = []

    for pname, keywords in portfolios.items():
        for kw in keywords:
            for variant in _expand_keyword(kw):
                pattern = r"\b" + re.escape(variant) + r"s?\b"
                if re.search(pattern, norm_text):
                    pmatches.add(pname)
                    actual_hits[pname].append(kw)
                    universe.append(kw)
                    break
    return pmatches, universe, actual_hits

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

# -------------------------------
# SAM query builder (helper)
# -------------------------------
def build_sam_params(args):
    """
    Build the query dict expected by request_sam().
    Keeps consistency between pipeline runs and sanity-check mode.
    """
    return {
        "url": "https://api.sam.gov/opportunities/v2/search",
        "from": args.from_date,
        "to": args.to_date,
        "limit": args.limit
    }

# -------------------- main --------------------

def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["prod","dev"], default="prod")
    ap.add_argument("--from", dest="from_date", default=(datetime.date.today()-datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
    ap.add_argument("--to", dest="to_date", default=datetime.date.today().strftime("%Y-%m-%d"))
    ap.add_argument("--limit", type=int, default=250)
    ap.add_argument("--query", default="cybersecurity OR analytics OR AI OR integration")
    ap.add_argument("--db", default=r"C:\CTS\Lead_Generation\data\cts_opportunities.db")
    ap.add_argument("--sam-api-key",dest="sam_api_key",help="Explicit SAM API key to use (overrides environment)",required=True)
    ap.add_argument("--filters-config", dest="filters_config", default=r"C:\CTS\Lead_Generation\configs\leadgen.cfg")
    ap.add_argument("--schema-sql", dest="schema_sql", default=r"C:\CTS\Lead_Generation\src\opportunities_schema.sql")
    ap.add_argument("--export-dir", default=r"E:\LeadGen\Logs")
    ap.add_argument("--overwrite-exports", dest="overwrite", type=str, default="true")
    ap.add_argument("--csv", action="store_true")
    ap.add_argument("--ndjson", action="store_true")
    ap.add_argument("--require-keyword-match", action="store_true")
    ap.add_argument("--source", choices=["sam"], default="sam")
    ap.add_argument("--fetch-summaries",dest="fetch_summaries",action="store_true",help="Fetch and store summary text from SAM.gov URLs")
    ap.add_argument("--sanity-check",action="store_true",help="Run in debug mode: fetch and display first few mapped opportunities"
)

    args = ap.parse_args()

    print(f"[INFO] Using SAM API key: {args.sam_api_key[:4]}...{args.sam_api_key[-4:]} (masked)")

    if not args.csv and not args.ndjson:
        args.csv = args.ndjson = True

    if not args.sam_api_key:
        env_name = "SAM_API_KEY_1" if args.profile == "prod" else "SAM_API_KEY_2"
        args.sam_api_key = os.environ.get(env_name, "")
        if not args.sam_api_key:
            print(f"ERROR: Env var {env_name} not found", file=sys.stderr)
            sys.exit(2)

    args.from_date = _iso(args.from_date) or datetime.date.today().strftime(DATE_FMT_OUT)
    args.to_date   = _iso(args.to_date) or datetime.date.today().strftime(DATE_FMT_OUT)
    overwrite = str(args.overwrite).lower() in {"1","true","yes","y"}
    cfg = _parse_cfg(args.filters_config)

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db)
    if args.schema_sql:
        _ensure_schema(conn, args.schema_sql)

    # sync portfolios table
    _sync_portfolios_to_db(conn, cfg["portfolios"])

    leads: List[Dict[str, Any]] = []
    raw_count = 0
    kept_count = 0

    if args.source == "sam":
        params = _sam_params(args)
        for raw in request_sam(params):
            raw_count += 1
            lead = map_sam_item_to_lead(raw)
            if not lead.get("opportunity_id"):
                continue

            lead["posted_date"] = _iso(lead.get("posted_date"))
            lead["due_date"] = _iso(lead.get("due_date"))
            lead["days_to_due"] = _days_to_due(lead["due_date"])

            text = (lead.get("title","") or "") + " " + (lead.get("summary","") or "")

            # portfolio + keyword hits
            pmatches, universe, actual_hits = _match_portfolios_and_hits(text, cfg["portfolios"])
            lead["portfolio"] = ";".join(pmatches) if pmatches else None
            lead["keywords"] = ";".join(sorted(set(universe))) if universe else None
            lead["keyword_hits"] = ";".join(sorted(set(actual_hits))) if actual_hits else None

            if args.require_keyword_match and not actual_hits:
                continue

            kept_count += 1
            lead["fit_score"] = compute_fit(lead, cfg)
            lead["risk_score"] = compute_risk(lead, cfg)
            lead["rev_hash"] = compute_rev_hash(
                lead.get("title",""), lead.get("due_date",""), int(lead.get("attachments_count") or 0)
            )
            upsert_opportunity(conn, lead)
            leads.append(lead)
    # Console
    if args.sanity_check:
        print("[DEBUG] Running map_sam_item_to_lead sanity check...")

        # minimal params object, same shape as normal run
        params = {
            "url": "https://api.sam.gov/opportunities/v2/search",
            "from": args.from_date,
            "to": args.to_date,
            "limit": args.limit
        }

        count = 0
        for raw in request_sam(params, api_key=args.sam_api_key):
            opp = map_sam_item_to_lead(raw)
            print(json.dumps(opp, indent=2)[:800])  # preview first 800 chars
            count += 1
            if count >= 3:  # only show first 3
                break

        print(f"[DEBUG] Displayed {count} mapped opportunities (sanity check mode)")
        return


    if args.export_dir and (args.csv or args.ndjson):
        export_dir = Path(args.export_dir) / "Opportunities" / datetime.date.today().strftime("%Y") / datetime.date.today().strftime("%m")
        _export_artifacts(leads, export_dir, "sam_opportunities", args.csv, args.ndjson, overwrite)

    pretty_fmt = "%d-%b-%y"
    print(json.dumps({
        "source": "sam",
        "from": datetime.datetime.strptime(args.from_date, DATE_FMT_OUT).strftime(pretty_fmt),
        "to": datetime.datetime.strptime(args.to_date, DATE_FMT_OUT).strftime(pretty_fmt),
        "raw_count": raw_count,
        "count": kept_count,
        "export_dir": args.export_dir,
        "csv": bool(args.csv),
        "ndjson": bool(args.ndjson)
    }))

print("[DEBUG] Running map_sam_item_to_lead sanity check...")


print(f"[DEBUG] Displayed {count} mapped opportunities")

# --- normal pipeline flow here ---
params = build_sam_params(args)
# continue with full ingestion/processing...

if __name__ == "__main__":
    main()
