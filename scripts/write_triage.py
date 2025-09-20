import sqlite3, argparse, datetime
from pathlib import Path

def generate_triage(db_path: str, out_dir: str, limit: int = 10, days_due: int = 14):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    today = datetime.date.today()
    tag = today.strftime("%d-%b-%y")

    md = []
    md.append(f"# CT Daily Triage — {tag}\n")

    # --- Top N by fit_score ---
    md.append("## Top Opportunities by Fit Score\n")
    md.append("| ID | Title | Portfolio | Keyword Hits | Agency | Due | Fit | Risk |")
    md.append("|----|-------|-----------|--------------|--------|-----|-----|------|")
    for row in c.execute(
        """
        SELECT opportunity_id, title, portfolio, keyword_hits, agency, due_date, fit_score, risk_score
        FROM opportunities
        ORDER BY fit_score DESC
        LIMIT ?
        """, (limit,)
    ):
        md.append(f"| {row[0]} | {row[1][:60]} | {row[2] or ''} | {row[3] or ''} | {row[4] or ''} | {row[5] or ''} | {row[6]:.2f} | {row[7]:.2f} |")

    # --- Due soon ---
    md.append(f"\n## Items Due Soon (≤ {days_due} days)\n")
    md.append("| ID | Title | Portfolio | Keyword Hits | Due | Days |")
    md.append("|----|-------|-----------|--------------|-----|------|")
    for row in c.execute(
        """
        SELECT opportunity_id, title, portfolio, keyword_hits, due_date,
               CAST((julianday(due_date) - julianday('now')) AS INT) AS days_left
        FROM opportunities
        WHERE due_date IS NOT NULL
          AND days_left <= ?
        ORDER BY due_date ASC
        """, (days_due,)
    ):
        md.append(f"| {row[0]} | {row[1][:60]} | {row[2] or ''} | {row[3] or ''} | {row[4] or ''} | {row[5]} |")

    # --- New from priority agencies ---
    md.append("\n## New Notices from Priority Agencies\n")
    md.append("| ID | Title | Portfolio | Keyword Hits | Agency | Posted |")
    md.append("|----|-------|-----------|--------------|--------|--------|")
    for row in c.execute(
        """
        SELECT opportunity_id, title, portfolio, keyword_hits, agency, posted_date
        FROM opportunities
        WHERE agency IN ('DHS','DOJ','HHS','VA')
        ORDER BY posted_date DESC
        LIMIT ?
        """, (limit,)
    ):
        md.append(f"| {row[0]} | {row[1][:60]} | {row[2] or ''} | {row[3] or ''} | {row[4]} | {row[5]} |")

    conn.close()

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(out_dir) / f"Daily_Triage_{today.strftime('%Y%m%d')}.md"
    Path(out_path).write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote triage report to {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--days-due", type=int, default=14)
    args = ap.parse_args()

    generate_triage(args.db, args.out_dir, args.limit, args.days_due)
