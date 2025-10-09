import argparse
import json
from sam_client import request_sam

# --- mapper function ---
def _first(d: dict, keys: list):
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return None

def map_sam_item_to_lead(raw: dict) -> dict:
    """Normalize a SAM.gov record into CTS schema."""
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

# --- main pipeline skeleton ---
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sam-api-key", required=True, help="SAM.gov API key")
    ap.add_argument("--from", dest="from_date", required=True, help="Posted from date (YYYY-MM-DD)")
    ap.add_argument("--to", dest="to_date", required=True, help="Posted to date (YYYY-MM-DD)")
    ap.add_argument("--limit", type=int, default=10, help="Max records to fetch")
    ap.add_argument("--query", dest="query", default="cybersecurity OR AI", help="Keyword query")
    args, unknown = ap.parse_known_args()
    if unknown:
        print(f"[WARN] Ignoring unrecognized args: {unknown}")


    params = {
        "from": args.from_date,
        "to": args.to_date,
        "limit": args.limit,
        "q": args.query
    }

    print(f"[INFO] Fetching SAM.gov opportunities {args.from_date} → {args.to_date}")

    count = 0
    for raw in request_sam(params, api_key=args.sam_api_key):
        opp = map_sam_item_to_lead(raw)
        print(json.dumps(opp, indent=2)[:800])  # preview first 800 chars
        count += 1
        if count >= 3:  # stop after 3 for sanity check
            break

    print(f"[INFO] Displayed {count} mapped opportunities")

if __name__ == "__main__":
    main()
