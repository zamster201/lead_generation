import numpy as np
import re
from sentence_transformers import SentenceTransformer
from fuzzywuzzy import fuzz
from datetime import datetime
import tomllib

# Load config & model (explicit for standalone runs)
with open("../configs/leadgen.toml", "rb") as f:
    config = tomllib.load(f)
KEYWORDS = config["filters"]["keywords"]
NAICS_CODES = config["filters"]["naics_codes"]
FIT_THRESHOLD = config["filters"]["fit_threshold"]
RISK_THRESHOLD = config["filters"]["risk_threshold"]
MIN_DAYS_TO_DUE = config["filters"]["min_days_to_due"]

model = SentenceTransformer('all-MiniLM-L6-v2')

def compute_days_to_due(deadline_str: str) -> int:
    if not deadline_str:
        return 0
    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        return (deadline - today).days
    except ValueError:
        return 0

def strict_keyword_match(title: str, description: str, naics: str) -> bool:
    """First-pass: Strict exact/partial match (no AI/fuzzy). Returns True if any keyword/NAICS hits."""
    text = f"{title} {description}".lower()
    # Exact substring or word-boundary match
    for kw in KEYWORDS:
        if re.search(rf'\b{re.escape(kw.lower())}\b', text) or kw.lower() in text:
            return True
    for code in NAICS_CODES:
        if code in str(naics):
            return True
    return False

def ai_enhanced_score(title: str, description: str, naics: str, parsed_doc_text: str = None) -> float:
    """AI layer: Fuzzy + semantic on base text + any parsed doc."""
    full_text = f"{title} {description} {parsed_doc_text or ''}".lower()
    # Fuzzy keywords (now on enriched text)
    keyword_scores = [fuzz.ratio(full_text, kw.lower()) for kw in KEYWORDS]
    keyword_fit = max(keyword_scores) if keyword_scores else 0
    naics_fit = 100 if any(code in str(naics) for code in NAICS_CODES) else 0
    # Semantic embeddings
    sentences = [full_text] + KEYWORDS
    embeddings = model.encode(sentences)
    if len(embeddings) > 1:
        cosine_sim = np.dot(embeddings[0], embeddings[1:]).max() / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1:]).max() + 1e-8)
        semantic_fit = cosine_sim * 100
    else:
        semantic_fit = 0
    return (0.4 * keyword_fit) + (0.3 * naics_fit) + (0.3 * semantic_fit)

def risk_score(soc: str, days_to_due: int) -> float:
    risk = 50.0
    if soc and 'small business' in soc.lower():
        risk -= 30
    if days_to_due > 60:
        risk -= 20
    elif days_to_due < 15:
        risk += 20
    return max(0, min(100, risk))

def should_triage(fit: float, risk: float, days_to_due: int) -> bool:
    return fit >= FIT_THRESHOLD and risk <= RISK_THRESHOLD and days_to_due >= MIN_DAYS_TO_DUE

# Test stub
if __name__ == "__main__":
    print(strict_keyword_match("Financial Cloud RFP", "Market data needed", "541511"))  # True
    print(ai_enhanced_score("Test", "Analytics", "541511", "Investment tools in doc"))  # ~75+