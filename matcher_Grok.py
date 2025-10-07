from fuzzywuzzy import fuzz
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    """Clean text for matching."""
    tokens = word_tokenize(text.lower())
    return ' '.join([w for w in tokens if w not in stop_words and len(w) > 2])

def score_relevance(description, keywords):
    """Score how well keywords match description (avg fuzzy ratio)."""
    desc_clean = preprocess_text(description)
    scores = [fuzz.ratio(desc_clean, kw) for kw in keywords]
    return max(scores)  # Or avg(scores) for broader match

def filter_opportunities(results, threshold=MATCH_THRESHOLD):
    """Filter results by relevance score."""
    filtered = []
    for opp in results:
        score = score_relevance(opp['description'], KEYWORDS)
        if score >= threshold:
            opp['relevance_score'] = score
            filtered.append(opp)
    return filtered