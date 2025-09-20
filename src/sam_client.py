from __future__ import annotations
import time, json, sys
from typing import Dict, Any, Iterator, List
import urllib.parse, urllib.request
import os
import itertools

BASE = "https://api.sam.gov/prod/opportunities/v2/search"

import os, time, urllib.request, urllib.error, itertools

# === Key setup ===
_API_KEY = None

def set_api_key(key_from_args=None):
    global API_KEY
    if key_from_args:
        API_KEY = key_from_args
    else:
        API_KEY = os.getenv("SAM_API_KEY_1")

    if not API_KEY:
        raise RuntimeError("No SAM API key provided (CLI or SAM_API_KEY_1 env var).")

def _http_get(url, attempt=1, backoff_ms=1000):
    """Perform GET request with exponential backoff (no key rotation)."""
    if not API_KEY:
        raise RuntimeError("API key not initialized. Call set_api_key() first.")

    req = urllib.request.Request(url, headers={"X-Api-Key": API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"[ERROR] API key over limit (429) with key ending {API_KEY[-6:]}")
            raise
        else:
            raise
    except Exception as e:
        if attempt < 3:
            sleep = backoff_ms / 1000.0
            print(f"[WARN] attempt {attempt} failed ({e}); retrying in {sleep}s...")
            time.sleep(sleep)
            return _http_get(url, attempt + 1, backoff_ms * 2)
        else:
            raise

def _build_query(params: Dict[str, Any]) -> str:
    q = {
        "api_key": params["api_key"],
        "limit": params.get("limit", 50),
        "postedFrom": params["from"],   # MM/DD/YYYY
        "postedTo": params["to"],       # MM/DD/YYYY
    }
    if params.get("q"):
        q["q"] = params["q"]
    return BASE + "?" + urllib.parse.urlencode(q)

def _extract_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    for k in ("opportunitiesData", "data", "results", "searchResults", "opportunities", "records"):
        v = payload.get(k)
        if isinstance(v, list) and v:
            return v
    for v in payload.values():
        if isinstance(v, list) and v:
            return v
        if isinstance(v, dict):
            for vv in v.values():
                if isinstance(vv, list) and vv:
                    return vv
    return []

import sys, time, urllib.error

def request_sam(params: Dict[str, Any], backoff_ms: int = 5000, max_retries: int = 8) -> Iterator[Dict[str, Any]]:
    # Build the query URL once
    url = _build_query(params)
    attempt = 1

    while True:
        try:
            payload = _http_get(url, attempt, backoff_ms)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # exponential backoff
                wait = (backoff_ms/1000.0) * (2 ** (attempt-1))
                sys.stderr.write(f"429: backing off {wait:.1f}s...\n")
                time.sleep(wait)
                attempt += 1
                if attempt > max_retries:
                    raise
            else:
                raise

    items = _extract_items(payload)
    if not items:
        sys.stderr.write("SAM payload keys: " + ", ".join(payload.keys()) + "\n")
    for it in items:
        yield it

def _first(raw: Dict[str, Any], names, default=None):
    for n in names:
        v = raw.get(n)
        if v not in (None, ""):
            return v
    return default

def _infer_vehicle(text: str) -> str:
    t = (text or "").upper()
    if "SEWP" in t: return "SEWP"
    if "CIO-SP3" in t or "CIOSP3" in t: return "CIO-SP3"
    if "GWAC" in t: return "GWAC"
    return ""

def map_sam_item_to_lead(raw: Dict[str, Any], fetch_summaries: bool = False) -> Dict[str, Any]:
    opp_id = _first(raw, ["id","noticeId","noticeID","solicitationNumber","solicitation_number","notice_number"])
    title  = _first(raw, ["title","noticeTitle","subject"])
    agency = _first(raw, ["agency","agencyName","organizationName","department","fullParentPathName"])
    due    = _first(raw, ["responseDate","dueDate","offersDueDate","response_deadline"])
    posted = _first(raw, ["postedDate","publishDate","datePosted","postedOn"])
    estval = _first(raw, ["estimatedValue","value","awardCeiling","ceiling","baseAndAllOptionsValue"])
    naics  = _first(raw, ["naics","naicsCode","primaryNaics","primaryNaicsCode"])
    setas  = _first(raw, ["setAside","typeOfSetAside","setAsideCode"])
    ctype  = _first(raw, ["typeOfContract","contractType"])

    # summary may just be a URL reference
    summary_url = _first(raw, ["description","summary","synopsis"])
    summary_text = ""

    if fetch_summaries and summary_url and summary_url.startswith("http"):
        try:
            req = urllib.request.Request(summary_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                summary_text = resp.read().decode("utf-8", errors="ignore")[:5000]  # keep it bounded
        except Exception as e:
            summary_text = f"[ERROR fetching summary: {e}]"

    url = _first(raw, ["uiLink","link","url","samLink","detailUrl"])
    atts = raw.get("attachments")
    acount = len(atts) if isinstance(atts, list) else 0
    vehicle = _first(raw, ["vehicle","contractVehicle"]) or _infer_vehicle((title or "") + " " + (summary_text or ""))

    return {
        "source": "sam",
        "opportunity_id": opp_id,
        "title": title,
        "agency": agency,
        "due_date": due,
        "posted_date": posted,
        "est_value": estval,
        "naics": naics,
        "set_aside": setas,
        "contract_type": ctype,
        "vehicle": vehicle,
        "summary_url": summary_url or "",
        "summary_text": summary_text or "",
        "url": url or "",
        "attachments_count": acount,
        "compliance_sections": int(raw.get("clausesCount") or 0),
        "is_multi_award": bool(raw.get("multipleAward") or False),
    }

