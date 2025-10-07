import sqlite3, argparse, datetime
from pathlib import Path

def generate_weekly(db_path: str, out_dir: str, week_offset: int = 0):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    today = datetime.date.today()
    iso_year, iso_week, iso_wday = today.isocalendar()
    week_num = iso_week - week_offset

    start = today - datetime.timedelta(days=iso_wday-1 + 7*week_offset)
    end   = start + datetime.timedelta(days=6)

    tag = f"{iso_year}-W{week_num:02d}"
    md = []
    md.append(f"# CT Weekly Opportunities — {tag}")
    md.append(f"_Window: {start.strftime('%d-%b-%y')} → {end.strftime('%d-%b-%y')}_\n")

    # --- High-fit ---
    md.append("## High-Fit Opportunities (≥ 0.70)\n")
    md.append("| ID | Title | Portfolio | Keyword Hits | Agency | Fit | Due |")
    md.append("|----|-------|-----------|--------------|--------|-----|-----|")
    for row in c.execute(
        """
        SELECT opportunity_id, title, portfolio, keyword_hits, agency, fit_score, due_date
        FROM opportunities
        WHERE fit_score >= 0.70
          AND posted_date BETWEEN ? AND ?
        ORDER BY fit_score DESC
        """, (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    ):
        md.append(f"| {row[0]} | {row[1][:60]} | {row[2] or ''} | {row[3] or ''} | {row[4] or ''} | {row[5]:.2f} | {row[6] or ''} |")

    # --- Portfolio breakdown ---
    md.append("\n## Portfolio Breakdown\n")
    for row in c.execute(
        """
        SELECT portfolio, COUNT(*)
        FROM opportunities
        WHERE posted_date BETWEEN ? AND ?
        GROUP BY portfolio
        ORDER BY COUNT(*) DESC
        """, (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    ):
        md.append(f"- {row[0]}: {row[1]} opportunities")

    # --- In-progress ---
    md.append("\n## In-Progress Items (qual/bid)\n")
    md.append("| ID | Title | Portfolio | Keyword Hits | Stage | Updated |")
    md.append("|----|-------|-----------|--------------|-------|---------|")
    for row in c.execute(
        """
        SELECT opportunity_id, title, portfolio, keyword_hits, status_stage, updated_at
        FROM opportunities
        WHERE status_stage IN ('qual','bid')
        ORDER BY updated_at DESC
        """):
        md.append(f"| {row[0]} | {row[1][:60]} | {row[2] or ''} | {row[3] or ''} | {row[4]} | {row[5]} |")

    conn.close()

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(out_dir) / f"CT_Weekly_Opportunities_{tag}.md"
    Path(out_path).write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote weekly rollup report to {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--week-offset", type=int, default=0)
    args = ap.parse_args()

    generate_weekly(args.db, args.out_dir, args.week_offset)
