import argparse
import datetime
from sam_client import request_sam
from collections import defaultdict

# --- mapper stub ---
def map_sam_item_to_lead(raw):
    """Minimal mapping from SAM.gov record to internal dict"""
    return {
        "id": raw.get("noticeId") or raw.get("id"),
        "title": raw.get("title") or raw.get("noticeTitle"),
        "agency": raw.get("agency") or raw.get("agencyName"),
        "due_date": raw.get("responseDate"),
        "posted_date": raw.get("postedDate"),
        "url": raw.get("uiLink"),
        "summary": raw.get("description") or "",
    }

def main():
    ap = argparse.ArgumentParser(description="Minimal SAM.gov pull pipeline")
    ap.add_argument("--sam-api-key", required=True, help="SAM.gov API key")
    ap.add_argument("--from", dest="from_date", default="2025-01-01",
                    help="Start date (YYYY-MM-DD)")
    ap.add_argument("--to", dest="to_date", default="2025-01-15",
                    help="End date (YYYY-MM-DD)")
    ap.add_argument("--limit", type=int, default=10,
                    help="Max results to fetch")
    args, _ = ap.parse_known_args()

    # --- Build params dict for request_sam ---
    params = {
        "from": args.from_date,
        "to": args.to_date,
        "limit": args.limit,
        "query": "cybersecurity OR AI"  # minimal default query
    }

    print(f"[INFO] Pulling SAM.gov opportunities "
          f"from {args.from_date} to {args.to_date}, limit={args.limit}")

    try:
        for raw in request_sam(params, api_key=args.sam_api_key):
            mapped = map_sam_item_to_lead(raw)
            print(mapped)
    except Exception as e:
        print(f"[ERROR] Failed to pull from SAM.gov: {e}")

def fetch_opportunities_multi(api_key, from_date, to_date, limit, keywords):
    """Query SAM.gov once per keyword, collect and deduplicate results."""

    all_results = []
    seen_ids = set()
    hit_counts = defaultdict(int)

    for kw in keywords:
        params = {
            "postedFrom": from_date,
            "postedTo": to_date,
            "limit": limit,
            "q": kw
        }

        print(f"[INFO] Querying keyword: {kw}")
        try:
            for raw in request_sam(params, api_key=api_key):
                opp_id = raw.get("id")
                if not opp_id:
                    continue

                hit_counts[kw] += 1

                # Dedup by ID
                if opp_id not in seen_ids:
                    seen_ids.add(opp_id)
                    all_results.append(raw)

        except Exception as e:
            print(f"[WARN] Query failed for keyword '{kw}': {e}")

    # Console hit summary
    print("\n[INFO] Keyword hit counts:")
    for kw, count in hit_counts.items():
        print(f"   {kw}: {count}")

    print(f"[INFO] Total unique opportunities collected: {len(all_results)}")
    return all_results

if __name__ == "__main__":
    main()
