import configparser
from fuzzywuzzy import fuzz
from datetime import datetime
import re

config = configparser.ConfigParser()
config.read('configs/leadgen.cfg')

KEYWORDS = [kw.strip() for kw in config['filters']['keywords'].split(',')]
NAICS_CODES = [code.strip() for code in config['filters']['naics_codes'].split(',')]
FIT_THRESHOLD = int(config['scoring']['fit_threshold'])
RISK_THRESHOLD = int(config['scoring']['risk_threshold'])
KEYWORD_WEIGHT = float(config['scoring']['keyword_weight'])
NAICS_WEIGHT = float(config['scoring']['naics_weight'])

def compute_days_to_due(deadline_str):
    """Compute days from today to deadline."""
    if not deadline_str:
        return None
    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        return (deadline - today).days
    except ValueError:
        return None

def fit_score(title, description, naics):
    """Score fit: weighted keyword + NAICS match."""
    text = f"{title} {description}".lower()
    keyword_scores = [fuzz.ratio(text, kw.lower()) for kw in KEYWORDS]
    keyword_fit = max(keyword_scores) if keyword_scores else 0
    
    naics_fit = 100 if any(code in naics for code in NAICS_CODES) else 0
    
    return (KEYWORD_WEIGHT * keyword_fit) + (NAICS_WEIGHT * naics_fit)

def risk_score(soc, days_to_due):
    """Simple risk: lower for small biz set-asides, more time."""
    risk = 50  # Base
    if soc and 'small business' in soc.lower():
        risk -= 30
    if days_to_due and days_to_due > 60:
        risk -= 20
    elif days_to_due and days_to_due < 15:
        risk += 20
    return max(0, min(100, risk))  # Clamp 0-100

def should_triage(fit, risk, days_to_due):
    """Filter for triage: good fit, low risk, upcoming."""
    min_days = int(config['filters']['min_days_to_due'])
    return (fit >= FIT_THRESHOLD and
            risk <= RISK_THRESHOLD and
            (days_to_due is None or days_to_due >= min_days))