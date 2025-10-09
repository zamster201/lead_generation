import os
import re
from datetime import datetime, timedelta
from typing import Dict, Optional
import tomllib

# Load config with robust path (works for direct run or import)
config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'leadgen.toml')
with open(config_path, "rb") as f:
    config = tomllib.load(f)

# Interpolate env vars (handles multiple if needed)
def interpolate_env(val):
    if isinstance(val, str) and '$env:' in val:
        env_key = val.split('$env:')[1].split()[0]  # Extract key like 'SAM_API_KEY_1'
        return os.environ.get(env_key, val)  # Fallback to literal if env var missing
    return val

# Apply to the config dict recursively (simple version for your sections)
for section in config:
    for key, value in config[section].items():
        config[section][key] = interpolate_env(value)

def strict_keyword_match(text: str, keywords: list) -> int:
    """Count exact keyword matches in text (case-insensitive)."""
    text_lower = text.lower()
    matches = sum(1 for kw in keywords if re.search(rf'\b{kw.lower()}\b', text_lower))
    return matches

def fit_score(text: str, keywords: list) -> float:
    """Normalized fit score (0.0-1.0) based on keyword density and matches."""
    if not text:
        return 0.0
    match_count = strict_keyword_match(text, keywords)
    text_words = len(re.findall(r'\w+', text.lower()))
    density = match_count / max(len(keywords), 1)  # Normalize by keywords
    if text_words > 0:
        density = min(density + (match_count / text_words), 1.0)  # Boost for density
    return density

def ai_enhanced_score(text: str, keywords: list) -> float:
    """Stub for AI scoring (e.g., via OpenAI embeddings similarity). Returns 0.0-1.0 fit."""
    # TODO: Integrate real AI; for now, enhance fit_score
    base_fit = fit_score(text, keywords)
    return min(base_fit * 1.2, 1.0)  # Slight boost for demo

def risk_score(lead: Dict) -> float:
    """Heuristic risk: 0.0 (low) to 1.0 (high). E.g., incumbent mentions, short deadline."""
    text = (lead.get('description', '') + ' ' + lead.get('parsed_doc_text', '')).lower()
    risk_factors = ['incumbent', 'current contractor', 'sole source']  # From config if expanded
    risk_hits = sum(1 for factor in risk_factors if factor in text)
    days_to_due = compute_days_to_due(lead)
    deadline_risk = 1.0 if days_to_due and days_to_due < 30 else 0.5 if days_to_due and days_to_due < 60 else 0.0
    return min((risk_hits * 0.2) + deadline_risk, 1.0)

def compute_days_to_due(lead: Dict) -> Optional[int]:
    """Days until response deadline; None if no deadline."""
    deadline_str = lead.get('response_deadline')
    if not deadline_str:
        return None
    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')  # Adjust format if needed
        return (deadline - datetime.now()).days
    except ValueError:
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M:%S')  # ISO alt
            return (deadline - datetime.now()).days
        except ValueError:
            return None

def should_triage(lead: Dict) -> bool:
    """Triage if overall score >= threshold and within filters (e.g., value, days)."""
    text = lead.get('description', '') + ' ' + lead.get('parsed_doc_text', '')
    fit = fit_score(text, config['filters']['keywords'])  # Use new fit_score
    risk = risk_score(lead)
    overall = (fit * config['scoring']['fit_weight']) + ((1 - risk) * config['scoring']['risk_weight'])

    days_to_due = compute_days_to_due(lead)
    value = lead.get('estimatedValue', 0)  # Assume from lead dict; fetch if needed
    within_days = days_to_due is None or (days_to_due <= config['filters']['max_days_to_due'] and days_to_due > 0)
    within_value = value >= config['filters']['min_value']
    no_excludes = not any(ex in text.lower() for ex in config['filters']['exclude_keywords'])

    return overall >= config['scoring']['threshold'] and within_days and within_value and no_excludes

# Test stub
if __name__ == "__main__":
    mock_lead = {
        "description": "Software development consulting IT services incumbent",
        "parsed_doc_text": "",
        "response_deadline": (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d %H:%M:%S'),
        "estimatedValue": 15000
    }
    print(f"Fit score: {fit_score(mock_lead['description'], config['filters']['keywords']):.2f}")
    print(f"Risk score: {risk_score(mock_lead):.2f}")
    print(f"Triage mock lead: {should_triage(mock_lead)}")
    print(f"Days to due: {compute_days_to_due(mock_lead)}")