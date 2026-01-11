import httpx
from bs4 import BeautifulSoup

PAYWALL_HINTS = [
    "subscribe", "subscription", "sign in to continue", "members-only", "paywall",
    "start your free trial", "trial", "upgrade to", "billing", "purchase",
    "join to read", "premium", "subscribe to read"
]

def _visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())

def fetch_page(url: str, max_chars: int) -> dict:
    """
    Fetch a page and return a small excerpt + paywall hint strings.
    Note: This is a basic fetcher. For production, add robots.txt compliance
    and stronger per-domain throttling.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; LearningItineraryBot/1.0)"
    }
    with httpx.Client(timeout=15, follow_redirects=True, headers=headers) as client:
        resp = client.get(url)

    content_type = resp.headers.get("content-type", "")
    if resp.status_code >= 400:
        return {
            "url": url,
            "status_code": resp.status_code,
            "content_type": content_type,
            "title": None,
            "excerpt": "",
            "paywall_signals": [],
        }

    # Only parse HTML pages
    if "text/html" not in content_type.lower():
        return {
            "url": url,
            "status_code": resp.status_code,
            "content_type": content_type,
            "title": None,
            "excerpt": "",
            "paywall_signals": [],
        }

    soup = BeautifulSoup(resp.text, "html.parser")
    title = (soup.title.string.strip() if soup.title and soup.title.string else None)
    text = _visible_text(soup)

    lower = text.lower()
    signals = [h for h in PAYWALL_HINTS if h in lower]
    excerpt = text[:max_chars]

    return {
        "url": url,
        "status_code": resp.status_code,
        "content_type": content_type,
        "title": title,
        "excerpt": excerpt,
        "paywall_signals": signals[:10],
    }
