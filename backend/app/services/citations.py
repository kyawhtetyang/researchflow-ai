from __future__ import annotations

from urllib.parse import urlparse


HIGH_TRUST_DOMAIN_MARKERS = (
    ".gov",
    ".edu",
    "nih.gov",
    "ncbi.nlm.nih.gov",
    "who.int",
    "worldbank.org",
    "oecd.org",
    "imf.org",
    "un.org",
    "europa.eu",
    "nature.com",
    "science.org",
    "sciencedirect.com",
    "springer.com",
    "arxiv.org",
    "jamanetwork.com",
    "sagepub.com",
)

MEDIUM_TRUST_DOMAIN_MARKERS = (
    ".org",
    "wikipedia.org",
    "bbc.com",
    "reuters.com",
    "apnews.com",
    "nytimes.com",
    "theguardian.com",
    "wsj.com",
    "ft.com",
)

LOW_TRUST_DOMAIN_MARKERS = (
    "medium.com",
    "substack.com",
    "blogspot.com",
    "wordpress.com",
    "wixsite.com",
    "tumblr.com",
    "pinterest.com",
    "instagram.com",
    "facebook.com",
    "tiktok.com",
    "reddit.com",
    "quora.com",
    "youtube.com",
)

EVIDENCE_POSITIVE_MARKERS = (
    "study",
    "studies",
    "research",
    "analysis",
    "survey",
    "report",
    "dataset",
    "journal",
    "paper",
    "evidence",
    "methodology",
    "findings",
    "statistics",
    "data",
)

EVIDENCE_NEGATIVE_MARKERS = (
    "buy now",
    "coupon",
    "sponsored",
    "affiliate",
    "shop now",
    "sign up",
    "subscribe",
    "free trial",
    "advertisement",
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def _hostname(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def _domain_score(hostname: str) -> float:
    host = hostname.lower()
    if not host:
        return 0.45
    if any(marker in host for marker in HIGH_TRUST_DOMAIN_MARKERS):
        return 0.95
    if any(marker in host for marker in MEDIUM_TRUST_DOMAIN_MARKERS):
        return 0.8
    if any(marker in host for marker in LOW_TRUST_DOMAIN_MARKERS):
        return 0.35
    return 0.62


def _evidence_score(title: str, content: str) -> float:
    text = f"{title}\n{content}".lower()
    score = 0.45

    content_length = len(content.strip())
    if content_length > 200:
        score += 0.08
    if content_length > 600:
        score += 0.1
    if content_length > 1600:
        score += 0.06

    positive_hits = sum(1 for marker in EVIDENCE_POSITIVE_MARKERS if marker in text)
    negative_hits = sum(1 for marker in EVIDENCE_NEGATIVE_MARKERS if marker in text)

    score += min(positive_hits, 5) * 0.06
    score -= min(negative_hits, 3) * 0.1

    return _clamp(score, 0.1, 0.95)


def _title_score(title: str) -> float:
    cleaned = title.strip()
    if not cleaned:
        return 0.3
    score = 0.45
    if len(cleaned) >= 18:
        score += 0.15
    if len(cleaned) >= 45:
        score += 0.1
    if any(marker in cleaned.lower() for marker in EVIDENCE_POSITIVE_MARKERS):
        score += 0.12
    return _clamp(score, 0.2, 0.9)


def _penalty(hostname: str, url: str, content: str) -> float:
    penalty = 0.0
    host = hostname.lower()
    text = content.lower()

    if any(marker in host for marker in LOW_TRUST_DOMAIN_MARKERS):
        penalty += 0.12
    if url.startswith("http://"):
        penalty += 0.03
    if len(content.strip()) < 120:
        penalty += 0.06
    if any(marker in text for marker in EVIDENCE_NEGATIVE_MARKERS):
        penalty += 0.08

    return penalty


def score_source_quality(source: dict) -> float:
    raw_score = _clamp(float(source.get("score") or 0.0), 0.0, 1.0)
    url = str(source.get("url") or "").strip()
    hostname = _hostname(url)
    title = str(source.get("title") or "").strip()
    content = str(source.get("content") or source.get("snippet") or "").strip()

    weighted = (
        raw_score * 0.45
        + _domain_score(hostname) * 0.3
        + _evidence_score(title, content) * 0.2
        + _title_score(title) * 0.05
    )
    adjusted = weighted - _penalty(hostname, url, content)

    # Keep the scale bounded and make perfect-looking scores rare in the UI.
    return round(_clamp(adjusted, 0.2, 0.97), 3)
