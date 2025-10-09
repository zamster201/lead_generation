from __future__ import annotations
import sqlite3, datetime
from pathlib import Path
import datetime

def _rows(conn, sql, args=()):
    cur = conn.execute(sql, args)
    cols = [d[0] for d in cur.description]
    for r in cur.fetchall():
        yield dict(zip(cols, r))

def _md_table(rows, cols):
    out = []
    out.append("| " + " | ".join(cols) + " |")
    out.append("|" + "|".join(["---"]*len(cols)) + "|")
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "") or "") for c in cols) + " |")
    return "\n".join(out)

def main(db_path: str, out_dir: str, top_n: int = 10, due_soon_days: int = 14):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    today = now.strftime("%d-%b-%y")     # 11-Sep-25
    hhmm = now.strftime("%H%M")
    triage_file = Path(out_dir) / f"Daily_Triage_{today}_{hhmm}.md"
    md = []
    md.append(f"# Daily Triage — {today} {now.strftime('%H:%M')}")
    with sqlite3.connect(db_path) as conn:
        top = list(_rows(conn, """
            SELECT opportunity_id, title, agency, due_date, fit_score, risk_score, status_stage, url
            FROM opportunities
            WHERE posted_date >= date('now','-30 day')
            ORDER BY fit_score DESC
            LIMIT ?
        """, (top_n,)))
        due = list(_rows(conn, """
            SELECT opportunity_id, title, agency, due_date, fit_score, risk_score, status_stage, url
            FROM opportunities
            WHERE due_date IS NOT NULL
            AND julianday(due_date) - julianday('now') <= ?
            AND status_stage IN ('new','screen','qual')
            ORDER BY due_date ASC
        """, (due_soon_days,)))
        prio = list(_rows(conn, """
            SELECT opportunity_id, title, agency, vehicle, due_date, fit_score, risk_score, status_stage, url
            FROM opportunities
            WHERE agency IN ('DHS','DOJ','HHS','VA') OR vehicle IN ('SEWP','CIO-SP3','GWAC')
            ORDER BY posted_date DESC
            LIMIT 20
        """))

    md = []
    md.append(f"# Daily Triage — {today}")
    md.append("\n## Top by Fit")
    md.append(_md_table(top, ["opportunity_id","title","agency","due_date","fit_score","risk_score","status_stage","url"]))
    md.append("\n## Due Soon (≤ 14 days)")
    md.append(_md_table(due, ["opportunity_id","title","agency","due_date","fit_score","risk_score","status_stage","url"]))
    md.append("\n## Priority Agencies/Vehicles")
    md.append(_md_table(prio, ["opportunity_id","title","agency","vehicle","due_date","fit_score","risk_score","status_stage","url"]))

    triage_file.write_text("\n".join(md), encoding="utf-8")
    print(str(triage_file))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to opportunities.db")
    ap.add_argument("--out", required=True, help="Output folder (e.g., E:/LeadGen/Logs/Outputs)")
    ap.add_argument("--top-n", type=int, default=10)
    ap.add_argument("--due-soon-days", type=int, default=14)
    args = ap.parse_args()
    main(args.db, args.out, args.top_n, args.due_soon_days)
