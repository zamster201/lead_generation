import requests
from bs4 import BeautifulSoup

def fetch_summary_text(url: str, max_chars: int = 5000) -> str:
    """
    Fetch the notice text from a SAM.gov summary/attachment URL.

    Args:
        url: The URL provided in the SAM.gov record.
        max_chars: Trim result so we don't overflow DB.

    Returns:
        Extracted text (truncated), or error string if failed.
    """
    if not url:
        return ""

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()

        # crude HTML stripping
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        return text[:max_chars]

    except Exception as e:
        return f"[ERROR fetching {url}: {e}]"
