 # Ingest Package

The `ingest` package handles **lead ingestion and output formatting** for the ClearTrend Lead Generation workspace.

---

## 📂 Files

- **`ingest_writer.py`**  
  Core writer function that outputs each lead in both:
  - `.json` → machine-readable, used by CE/SVT pipelines
  - `.md`   → CTS-compliant frontmatter, browsable in Obsidian

- **`dummy_data.py`**  
  Generates placeholder leads for testing the pipeline before real RFP sources are wired in.

- **`__init__.py`**  
  Makes this a proper Python package.

---

## ⚡ Usage

### Write a single lead
```python
from ingest import ingest_writer

lead = {
    "title": "Cybersecurity SOC Expansion",
    "agency": "US Air Force",
    "due_date": "2025-09-30",
    "keywords": ["cybersecurity", "darktrace"],
    "value_estimate": "$3M"
}

files = ingest_writer.write_lead(lead, lead_id="lead_test")
print(files)
