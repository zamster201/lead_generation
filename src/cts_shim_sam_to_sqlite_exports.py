
import os
import re
import sqlite3
from datetime import datetime
from typing import List, Dict, Any

import requests
import pandas as pd

API_KEY = os.getenv("SAM_API_KEY", "")
DB_PATH = os.getenv("CT_DB_PATH", "leads.db")
EXPORT_DIR = os.getenv("CT_EXPORT_DIR", "exports")
QUERY = os.getenv("CT_QUERY", "cybersecurity")
DATE_FROM = os.getenv("CT_POSTED_FROM", "")
DATE_TO = os.getenv("CT_POSTED_TO", "")
LIMIT = int(os.getenv("CT_LIMIT", "100"))

URL_RE = re.compile(r"https?://[^\s)>\]\"']+", re.IGNORECASE)

def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def yyyymmdd(d: str) -> str:
    try:
        return datetime.fromisoformat(d.replace("Z","").replace("T"," ")).strftime("%Y%m%d")
    except Exception:
        return ""

def clean_src(src: str) -> str:
    return src.replace(".","").replace("_","").replace("/","").replace(" ","").upper()

def build_ct_id(source: str, posted_iso: str, id_: str) -> str:
    if not (source and posted_iso and id_):
        return ""
    stamp = yyyymmdd(posted_iso)
    if not stamp:
        return ""
    return f"CT-{clean_src(source)}-{stamp}-{id_}".upper()

def extract_doc_urls(item: Dict[str, Any]) -> List[str]:
    urls = []
    for k in ("resourceLinks","links","attachments","documents","fileUrls","urls"):
        v = item.get(k)
        if isinstance(v, list):
            for e in v:
                if isinstance(e, str) and e.startswith("http"):
                    urls.append(e)
                elif isinstance(e, dict):
                    for kk in ("url","link","href","downloadUrl"):
                        u = e.get(kk)
                        if isinstance(u, str) and u.startswith("http"):
                            urls.append(u)
    for text_key in ("description","summary","text","body","solicitationDescription"):
        txt = item.get(text_key)
        if isinstance(txt, str) and "http" in txt:
            urls += URL_RE.findall(txt)
    # dedupe
    out, seen = [], set()
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out

def init_db(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id TEXT PRIMARY KEY,
        ct_id TEXT,
        title TEXT,
        agency TEXT,
        posted TEXT,
        due TEXT,
        keywords TEXT,
        value_estimate TEXT,
        source TEXT,
        created TEXT,
        edited TEXT,
        status TEXT,
        product_match TEXT,
        feature TEXT,
        priority TEXT,
        partner_strategy TEXT,
        wf_status TEXT,
        active TEXT,
        next_action_date TEXT,
        owner TEXT,
        notes TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id TEXT,
        url TEXT,
        label TEXT,
        FOREIGN KEY(lead_id) REFERENCES leads(id)
    )
    """)
    conn.commit()

def upsert_lead(conn: sqlite3.Connection, row: Dict[str, Any]):
    cur = conn.cursor()
    cols = list(row.keys())
    placeholders = ",".join(["?"]*len(cols))
    update_clause = ",".join([f"{c}=excluded.{c}" for c in cols if c!="id"])
    sql = f"INSERT INTO leads ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {update_clause}"
    cur.execute(sql, [row[c] for c in cols])

def insert_documents(conn: sqlite3.Connection, lead_id: str, urls: List[str]):
    if not urls: return
    cur = conn.cursor()
    for u in urls:
        cur.execute("INSERT INTO documents (lead_id, url, label) VALUES (?,?,?)", (lead_id, u, ""))

def fetch_sam(query: str, limit: int, posted_from: str, posted_to: str):
    if not API_KEY:
        raise SystemExit("Missing SAM_API_KEY in environment. In PowerShell: $env:SAM_API_KEY='YOUR_KEY'")
    url = "https://api.sam.gov/prod/opportunities/v2/search"
    params = {"api_key": API_KEY, "limit": limit}
    if query: params["q"] = query
    if posted_from: params["postedFrom"] = posted_from
    if posted_to: params["postedTo"] = posted_to
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json().get("opportunitiesData", []) or []

def normalize_sam_item(item: Dict[str, Any]) -> Dict[str, Any]:
    lead = {
        "id": item.get("noticeId") or item.get("solicitationNumber") or item.get("id") or "",
        "title": item.get("title") or "",
        "agency": item.get("agency") or item.get("department") or "",
        "posted": item.get("postedDate") or item.get("publishDate") or "",
        "due": item.get("responseDeadLine") or item.get("responseDate") or "",
        "keywords": ",".join(item.get("naicsCodes", []) or []),
        "value_estimate": item.get("baseType") or "Unknown",
        "source": "sam.gov",
        "created": now_ts(),
        "edited": now_ts(),
        "status": None,
        "product_match": None,
        "feature": None,
        "priority": None,
        "partner_strategy": None,
        "wf_status": "unfiled",
        "active": "Active",
        "next_action_date": None,
        "owner": None,
        "notes": None
    }
    lead["ct_id"] = build_ct_id(lead["source"], lead["posted"], lead["id"])
    return lead

def export_csv(conn: sqlite3.Connection, out_path: str):
    df = pd.read_sql_query("""
        SELECT l.*,
               GROUP_CONCAT(d.url, ' | ') AS doc_urls
        FROM leads l
        LEFT JOIN documents d ON l.id = d.lead_id
        GROUP BY l.id
        ORDER BY l.posted DESC
    """, conn)
    df.to_csv(out_path, index=False, encoding="utf-8")

def export_xlsx(conn: sqlite3.Connection, out_path: str):
    df = pd.read_sql_query("""
        SELECT l.*,
               GROUP_CONCAT(d.url, ' | ') AS doc_urls
        FROM leads l
        LEFT JOIN documents d ON l.id = d.lead_id
        GROUP BY l.id
        ORDER BY l.posted DESC
    """, conn)
    df.to_excel(out_path, index=False)

def export_md(conn: sqlite3.Connection, out_dir: str):
    import os
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_sql_query("""
        SELECT l.*,
               GROUP_CONCAT(d.url, ' | ') AS doc_urls
        FROM leads l
        LEFT JOIN documents d ON l.id = d.lead_id
        GROUP BY l.id
        ORDER BY l.posted DESC
    """, conn)
    for _, r in df.iterrows():
        created = r["created"] or now_ts()
        edited = r["edited"] or now_ts()
        source = r["source"] or "sam.gov"
        wf = r["wf_status"] or "unfiled"
        tags = f'["lead","{source}"]'
        title = r["title"] or "Untitled"
        doc_urls = (r["doc_urls"] or "").strip()
        frontmatter = f"""created: {created}
edited: {edited}
origin: {source}
source: {source}
wf_status: {wf}
tags: {tags}
"""
        body = f"""# {title}

**ID**: {r['id']}
**CT ID**: {r.get('ct_id','')}
**Agency**: {r.get('agency','')}
**Posted**: {r.get('posted','')}
**Due**: {r.get('due','')}
**Source**: {source}
**Value Estimate**: {r.get('value_estimate','')}
**Active**: {r.get('active','')}

---

### Keywords
{r.get('keywords','')}

### Documents / Links
{doc_urls if doc_urls else '(none detected)'}

### Notes
{r.get('notes','') or ''}
"""
        fname = f"{(r['ct_id'] or r['id']).replace('/','-')}.md"
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
            f.write(frontmatter + "\n---\n\n" + body)

def main():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    items = fetch_sam(QUERY, LIMIT, DATE_FROM, DATE_TO)
    for it in items:
        lead = normalize_sam_item(it)
        if not lead["id"]:
            continue
        upsert_lead(conn, lead)
        urls = extract_doc_urls(it)
        insert_documents(conn, lead["id"], urls)

    conn.commit()
    stamp = datetime.now().strftime("%d-%b-%y")
    export_csv(conn, os.path.join(EXPORT_DIR, f"leads_{stamp}.csv"))
    export_xlsx(conn, os.path.join(EXPORT_DIR, f"leads_{stamp}.xlsx"))
    export_md(conn, os.path.join(EXPORT_DIR, f"md_{stamp}"))
    conn.close()
    print(f"Done. DB: {DB_PATH} | Exports in: {EXPORT_DIR}")

if __name__ == "__main__":
    main()
