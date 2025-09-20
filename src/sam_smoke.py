#!/usr/bin/env python3
import argparse, json
from sam_client import request_sam, map_sam_item_to_lead
import datetime

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sam-api-key", required=True)
    ap.add_argument("--from", dest="from_date", required=True, help="MM/DD/YYYY")
    ap.add_argument("--to", dest="to_date", required=True, help="MM/DD/YYYY")
    ap.add_argument("--q", dest="q", default="")
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    params = {"api_key": args.sam_api_key, "from": args.from_date, "to": args.to_date, "q": args.q, "limit": args.limit}
    n = 0
    for raw in request_sam(params):
        lead = map_sam_item_to_lead(raw)
        print(json.dumps({k: lead.get(k) for k in ("opportunity_id","title","agency","posted_date","due_date","url")}, ensure_ascii=False))
        n += 1
        if n >= args.limit:
            break
    if n == 0:
        print("No items returned. Try widening date window or dropping --q.")

if __name__ == "__main__":
    main()
