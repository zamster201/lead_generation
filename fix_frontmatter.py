#!/usr/bin/env python3
import argparse, re, sys, json
from pathlib import Path
from datetime import datetime

FRONTMATTER_RX = re.compile(r"\A\ufeff?\s*---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
KV_LINE_RX = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*[:\-]\s*(.+?)\s*$")
ISO_RX = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$")

DEFAULT_TAGS = ["lead_generation"]   # add your defaults here if you want

def parse_yaml_block(text:str) -> dict:
    """Very small YAML-ish parser (frontmatter only: scalars + simple lists)."""
    data = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1; continue
        m = KV_LINE_RX.match(line)
        if not m:
            i += 1; continue
        k, v = m.group(1).strip(), m.group(2).strip()
        if v.startswith("[") and v.endswith("]"):
            # crude list: ["a","b"] or [a, b]
            vals = [x.strip().strip('"\'' ) for x in re.split(r",\s*", v[1:-1]) if x.strip()]
            data[k] = vals
        else:
            data[k] = v.strip('"\'')

        i += 1
    return data

def dump_yaml_block(d:dict) -> str:
    def fmt_val(v):
        if isinstance(v, list):
            inner = ", ".join([json.dumps(x) for x in v])
            return f"[{inner}]"
        return json.dumps(v)
    lines = [f"{k}: {fmt_val(v)}" for k, v in d.items()]
    return "---\n" + "\n".join(lines) + "\n---\n"

def infer_defaults(md_path: Path) -> dict:
    # Infer wf_status from folder
    p = [x.lower() for x in md_path.parts]
    wf = "reference"
    if "runbooks" in p: wf = "runbook"
    elif "logs" in p: wf = "log"
    elif "outputs" in p: wf = "report"
    elif "partners" in p: wf = "unfiled"
    meta = {
        "origin": "leadgen",
        "source": "external",
        "wf_status": wf,
        "tags": DEFAULT_TAGS.copy()
    }
    # created/edited from filesystem times if you want a seed
    try:
        stat = md_path.stat()
        created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M")
        edited  = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        meta["created"] = created
        meta["edited"]  = edited
    except Exception:
        pass
    return meta

def _normalize_ts(s: str) -> str:
    # Accept "Aug-25-2025 21:52" and ISO; return ISO "YYYY-MM-DD HH:MM"
    for fmt in ("%b-%d-%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass
    return s  # leave as-is if unknown
    
def normalize(meta: dict, md_path: Path) -> dict:
    implied = infer_defaults(md_path)
    for k, v in implied.items():
        meta.setdefault(k, v)

    # casing & canonical values
    for k in ("origin", "source", "wf_status"):
        if k in meta and isinstance(meta[k], str):
            meta[k] = meta[k].strip().lower()

    # align origin to vault convention
    if meta.get("origin") not in ("leadgen",):
        meta["origin"] = "leadgen"

    # timestamps
    for k in ("created", "edited"):
        if k in meta and isinstance(meta[k], str):
            meta[k] = _normalize_ts(meta[k])

    # tags to list + de-dup
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [t for t in re.split(r"[,\s]+", tags) if t]
    if "lead_generation" not in [t.lower() for t in tags]:
        tags.append("lead_generation")
    meta["tags"] = tags
    return meta

def fix_file(md_path: Path, dry_run: bool=False) -> str:
    text = md_path.read_text(encoding="utf-8", errors="ignore")

    fm_match = FRONTMATTER_RX.match(text)
    if fm_match:
        # normalize existing
        front_block = fm_match.group(1)
        meta = parse_yaml_block(front_block)
        meta = normalize(meta, md_path)
        new_fm = dump_yaml_block(meta)
        new_text = FRONTMATTER_RX.sub(lambda m: new_fm, text, count=1)
        changed = (new_text != text)
    else:
        # attempt to scrape "property-like" lines near top (first 60 lines)
        head = "\n".join(text.splitlines()[:60])
        meta = {}
        for line in head.splitlines():
            m = KV_LINE_RX.match(line)
            if m:
                meta[m.group(1).strip().lower()] = m.group(2).strip()
        meta = normalize(meta, md_path)
        new_fm = dump_yaml_block(meta)
        new_text = new_fm + text
        changed = True

    if changed and not dry_run:
        bak = md_path.with_suffix(md_path.suffix + ".bak")
        if not bak.exists():
            bak.write_text(text, encoding="utf-8")
        md_path.write_text(new_text, encoding="utf-8")
        return "updated"
    return "ok"

def main():
    ap = argparse.ArgumentParser(description="Bulk-fix YAML frontmatter in Obsidian notes for LeadGen.")
    ap.add_argument("--root", required=True, help="Path to vault (e.g., E:\\LeadGen)")
    ap.add_argument("--dry-run", action="store_true", help="Analyze only; do not modify files")
    ap.add_argument("--glob", default="**/*.md", help="Glob pattern (default **/*.md)")
    args = ap.parse_args()

    root = Path(args.root)
    count = upd = 0
    for p in root.glob(args.glob):
        if not p.is_file():
            continue
        count += 1
        result = fix_file(p, dry_run=args.dry_run)
        if result == "updated":
            upd += 1
        print(f"[{result}] {p}")

    print(f"\n[SUMMARY] scanned={count} updated={upd} dry_run={args.dry_run}")

if __name__ == "__main__":
    sys.exit(main())
