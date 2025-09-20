import argparse
from ingest import ingest_writer

# Example dummy lead templates
DUMMY_TEMPLATES = [
    {
        "title": "Cybersecurity Monitoring RFP",
        "agency": "Department of Homeland Security",
        "due_date": "2025-09-15",
        "keywords": ["cybersecurity", "darktrace", "network"],
        "value_estimate": "$2M"
    },
    {
        "title": "Voice Analytics Platform",
        "agency": "Department of Justice",
        "due_date": "2025-09-22",
        "keywords": ["voice", "audivi", "analytics"],
        "value_estimate": "$800K"
    },
    {
        "title": "High-Speed Storage Expansion",
        "agency": "Department of Energy",
        "due_date": "2025-10-01",
        "keywords": ["storage", "kove", "HPC"],
        "value_estimate": "$5M"
    }
]

def generate_dummy_leads(count: int, prefix: str = None):
    """
    Generate a batch of dummy leads.
    Cycles through templates and appends an index to make them unique.
    Optionally apply a prefix to the lead_id for easier batch tracking.
    """
    written = []
    for i in range(count):
        template = DUMMY_TEMPLATES[i % len(DUMMY_TEMPLATES)].copy()
        # Make title unique
        template["title"] = f"{template['title']} #{i+1}"
        
        # If prefix is provided, prepend it to lead_id
        if prefix:
            lead_id = f"{prefix}_{i+1}"
            files = ingest_writer.write_lead(template, lead_id=lead_id)
        else:
            files = ingest_writer.write_lead(template)
        
        written.append(files)
    return written

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dummy leads for testing.")
    parser.add_argument("--count", type=int, default=3, help="Number of dummy leads to generate")
    parser.add_argument("--prefix", type=str, help="Optional prefix for batch (e.g., DEVTEST)")
    args = parser.parse_args()

    results = generate_dummy_leads(args.count, args.prefix)
    for r in results:
        print("Created:", r)
