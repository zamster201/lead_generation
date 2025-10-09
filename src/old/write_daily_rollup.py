from __future__ import annotations
import sqlite3, datetime
from pathlib import Path

def _rows(conn, sql, args=()):
    cur = conn.execute(sql, args); cols = [d[0] for d in cur.description]
    for r in cur.fetchall(): yield dict(zip(cols, r))

def _md_table(rows, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"]*len(cols)) + "|"]
    for r in rows: out.append("| " + " | ".join(str(r.get(c,"") or "") for c in cols) + " |")
    return "\n".join(out)

def main(db_path: str, out_dir: str, top_n: int = 25, fit_cut: float = 0.75):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    tag = now.strftime("%d-%b-%y")  # << your format (e.g., 10-Sep-25)
    out = Path(out_dir) / f"CT_Weekly_Opportunities_{tag}.md"

    # define week window (Sat..Fri feels natural for gov feeds; adjust if needed)
    end = now.date()
    start = end - datetime.timedelta(days=6)

    with sqlite3.connect(db_path) as conn:
        # high-fit new this week
        high_new = list(_rows(conn, """
            SELECT opportunity_id, title, agency, due_date, fit_score, status_stage, url
            FROM opportunities
            WHERE fit_score >= ? AND date(posted_date) BETWEEN date(?) AND date(?)
            ORDER BY fit_score DESC, posted_date DESC
            LIMIT ?
        """, (fit_cut, start.isoformat(), end.isoformat(), top_n)))

        # in-progress (qual/bid) regardless of posted date
        in_prog = list(_rows(conn, """
            SELECT opportunity_id, title, agency, due_date, fit_score, status_stage, url
            FROM opportunities
            WHERE status_stage IN ('qual','bid')
            ORDER BY due_date ASC NULLS LAST, fit_score DESC
            LIMIT 50
        """))

        # changed this week (revision bumped or updated_at in window)
        changed = list(_rows(conn, """
            SELECT opportunity_id, title, agency, due_date, fit_score, revision, status_stage, url, updated_at
            FROM opportunities
            WHERE date(updated_at) BETWEEN date(?) AND date(?)
              AND revision > 0
            ORDER BY updated_at DESC
            LIMIT 50
        """, (start.isoformat(), end.isoformat())))

    md = []
    md.append(f"# CT Weekly Opportunities — {tag}")
    md.append(f"_Window: {start.strftime('%d-%b-%y')} → {end.strftime('%d-%b-%y')}_\n")

    md.append("## New High-Fit (this week)")
    md.append(_md_table(high_new, ["opportunity_id","title","agency","due_date","fit_score","status_stage","url"]))

    md.append("\n## In-Progress (qual/bid)")
    md.append(_md_table(in_prog, ["opportunity_id","title","agency","due_date","fit_score","status_stage","url"]))

    md.append("\n## Changes (updated this week)")
    md.append(_md_table(changed, ["opportunity_id","title","agency","due_date","fit_score","revision","status_stage","updated_at","url"]))

    out.write_text("\n".join(md), encoding="utf-8")
    print(str(out))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True, help="Folder for weekly rollups (e.g., E:/LeadGen/Logs/Outputs)")
    ap.add_argument("--top-n", type=int, default=25)
    ap.add_argument("--fit-cut", type=float, default=0.75)
    args = ap.parse_args()
    main(args.db, args.out, args.top_n, args.fit_cut)
