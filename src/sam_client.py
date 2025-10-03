import urllib.request
import json
from urllib.parse import urlencode

def _http_get(url, headers, timeout=45):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def request_sam(params, api_key):
    """
    Query the SAM.gov API for opportunities using clean URL encoding.
    params should be a dict with keys: from, to, limit, query
    """
    base_url = "https://api.sam.gov/opportunities/v2/search"

    # Build safe query string
    query = {
        "postedFrom": params.get("from"),
        "postedTo": params.get("to"),
        "limit": params.get("limit", 50),
        "q": params.get("query", "")
    }
    url = f"{base_url}?{urlencode(query)}"

    headers = {"X-Api-Key": api_key}

    # DEBUG: show the final request URL and headers
    print(f"[DEBUG] Requesting URL: {url}")
    print(f"[DEBUG] Using headers: {headers}")

    return _http_get(url, headers)
