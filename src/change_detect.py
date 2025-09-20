from __future__ import annotations
import hashlib, sqlite3
from typing import Dict, Any

def compute_rev_hash(title: str, due_date: str, attachments_count: int) -> str:
    basis = f"{title}|{due_date}|{attachments_count}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()

def upsert_opportunity(conn: sqlite3.Connection, lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upsert by (source, opportunity_id). If rev_hash changes, increment revision.
    Preserve human-updated status_stage if it already exists.
    """
    cur = conn.execute(
        "SELECT id, rev_hash, revision, status_stage FROM opportunities WHERE source=? AND opportunity_id=?",
        (lead["source"], lead["opportunity_id"]),
    )
    row = cur.fetchone()
    new_hash = lead.get("rev_hash")
    if row:
        oid, old_hash, old_rev, old_stage = row
        revision = (old_rev or 0) + (1 if old_hash != new_hash else 0)
        if old_stage:
            lead["status_stage"] = old_stage
        fields = [
            "title","agency","due_date","posted_date","est_value","naics","set_aside",
            "contract_type","vehicle","keywords","url","attachments_count","compliance_sections",
            "fit_score","risk_score","rev_hash"
        ]
        sets = ", ".join([f"{f}=?" for f in fields] + ["revision=?", "updated_at=datetime('now')"])
        vals = [lead.get(f) for f in fields] + [revision, oid]
        conn.execute(f"UPDATE opportunities SET {sets} WHERE id=?", vals)
        conn.commit()
        return {"updated": 1, "inserted": 0, "revision_changed": int(old_hash != new_hash)}
    else:
        fields = [
            "source","opportunity_id","title","agency","due_date","posted_date","est_value","naics",
            "set_aside","contract_type","vehicle","keywords","url","attachments_count",
            "compliance_sections","fit_score","risk_score","status_stage","rev_hash","revision"
        ]
        vals = [lead.get(f) for f in fields]
        conn.execute(
            f"INSERT INTO opportunities ({','.join(fields)}) VALUES ({','.join(['?']*len(fields))})",
            vals,
        )
        conn.commit()
        return {"updated": 0, "inserted": 1, "revision_changed": 0}
