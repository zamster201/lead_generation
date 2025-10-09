import sqlite3
from src.fetcher import fetch_sam_opps, map_to_lead
from src.scorer import strict_keyword_match, ai_enhanced_score, risk_score, compute_days_to_due, should_triage
from src.detector import has_changed
from src.storage import init_db, upsert_lead
from src.triage import query_triagable, write_triage
import tomllib

# Load config for thresholds
with open("configs/leadgen.toml", "rb") as f:
    config = tomllib.load(f)

def main():
    init_db()
    # First pass: Fetch + strict keyword filter (no AI)
    raw_opps = fetch_sam_opps(parse_attachments=False)  # Skip parse initially for speed
    leads = [map_to_lead(item) for item in raw_opps if item.get("id")]
    strict_filtered = [lead for lead in leads if strict_keyword_match(lead["title"], lead["description"], lead["naics"])]

    if not strict_filtered:
        print("No keyword matches in first pass.")
        return

    print(f"Strict filter: {len(strict_filtered)} / {len(leads)} leads proceed to parse/AI.")

    # Second pass: Re-fetch/parse attachments for filtered leads (targeted, not bulk)
    sam_ids = [lead["sam_id"] for lead in strict_filtered]
    # Note: For real, query SAM by ID for attachments; mock here
    enriched_opps = fetch_sam_opps(parse_attachments=True)  # Full fetch with parse (or optimize to ID-specific)
    enriched_map = {opp["id"]: opp for opp in enriched_opps}
    for lead in strict_filtered:
        if lead["sam_id"] in enriched_map:
            lead["parsed_doc_text"] = enriched_map[lead["sam_id"]].get("parsed_doc_text", "")

    # AI scoring on enriched
    for lead in strict_filtered:
        lead["fit_score"] = ai_enhanced_score(lead["title"], lead["description"], lead["naics"], lead["parsed_doc_text"])
        lead["risk_score"] = risk_score(lead["soc"], compute_days_to_due(lead["response_deadline"]))
        lead["days_to_due"] = compute_days_to_due(lead["response_deadline"])

    # Upsert changed
    conn = sqlite3.connect("opps.db")
    updated = 0
    for lead in strict_filtered:
        if has_changed(conn, lead):
            upsert_lead(conn, lead)
            updated += 1
    conn.close()
    print(f"AI-enriched: {updated} updated.")

    # Triage
    triaged_leads = query_triagable()
    write_triage(triaged_leads)

if __name__ == "__main__":
    init_db()  # Setup DB
    print("Fetching SAM opps...")
    opps = fetch_sam_opps(parse_attachments=True)  # Enable parsing
    leads = [map_to_lead(opp) for opp in opps]
    print(f"Fetched {len(leads)} leads")
    triaged = triaged_leads(leads)
    print(f"Triaged {len(triaged)} hot leads (keyword matches: see scores)")
    if triaged:
        output = write_triage(triaged)
        print(f"Exported to {output}")
    else:
        print("No matches—tune keywords/dates in config!")
    # Bonus: Query triagable for next run
    triagable = query_triagable()
    print(f"{len(triagable)} triagable leads in DB")