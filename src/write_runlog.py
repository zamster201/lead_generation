
#!/usr/bin/env python3
import sys, json, os, datetime as dt
from pathlib import Path

def write_runlog(summary: dict, out_dir: Path, fmt: str = "md"):
    now = dt.datetime.now()
    sub = out_dir / now.strftime("%Y") / now.strftime("%m")
    sub.mkdir(parents=True, exist_ok=True)
    ts = now.strftime("%Y%m%d_%H%M")
    written = []

    if fmt in ("md","both"):
        md = sub / f"run_{ts}.md"
        body = [
            "---",
            f"created: {now.strftime('%Y-%m-%d %H:%M')}",
            "origin: leadgen",
            "source: cts_pipeline",
            "wf_status: log",
            'tags: ["log","run","lead_generation"]',
            "---\n",
            f"# Run Log — {now.strftime('%Y-%m-%d %H:%M')}\n",
            "**Summary**",
            f"- Source: {summary.get('source','')}",
            f"- Ingested: {summary.get('ingested',0)}",
            f"- DB added: {summary.get('db_added',0)}",
            f"- DB updated: {summary.get('db_updated',0)}",
            f"- Artifacts written: {summary.get('artifacts_written',0)}",
            f"- Export dir: {summary.get('export_dir','')}",
            "\n**Notes**",
            "- ",
            ""
        ]
        md.write_text("\n".join(body), encoding="utf-8")
        written.append(str(md))

    if fmt in ("json","both"):
        jf = sub / f"run_{ts}.json"
        jf.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        written.append(str(jf))

    return written

def main():
    # Args: out_dir [fmt]
    if len(sys.argv) < 2:
        print("Usage: write_runlog.py <out_dir> [md|json|both]", file=sys.stderr)
        return 2
    out_dir = Path(sys.argv[1])
    fmt = sys.argv[2].lower() if len(sys.argv) > 2 else "md"

    # Read JSON summary from stdin
    try:
        text = sys.stdin.read()
        summary = json.loads(text)
    except Exception as e:
        print(f"[ERROR] Expected JSON on stdin: {e}", file=sys.stderr)
        return 1

    paths = write_runlog(summary, out_dir, fmt)
    print(json.dumps({"written": paths}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
