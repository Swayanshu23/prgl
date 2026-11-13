"""
Preprocessing module: normalize, transliterate, strip affixes.
"""
import re
import unicodedata
from typing import List, Dict

AFFIXES = {
    "the", "a", "an", "india", "indian", "national", "samachar", "news",
    "times", "herald", "chronicle", "express", "tribune", "gazette", "patrika",
    "darpan", "sandesh", "prabhat", "sandhya", "daily", "new", "morning",
    "evening", "weekly", "monthly",
}

PERIODICITY_WORDS = {
    "daily", "weekly", "monthly", "quarterly", "annual", "biweekly",
    "fortnightly", "bi-weekly", "yearly", "pratidin", "saptahik", "masik",
}


def normalize(text: str) -> str:
    """Lowercase, strip punctuation, normalize unicode to ASCII."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_affixes(title: str) -> str:
    """Remove common stopword affixes from a title for cleaner comparison."""
    words = normalize(title).split()
    filtered = [w for w in words if w not in AFFIXES]
    return " ".join(filtered).strip() or normalize(title)


def strip_periodicity(title: str) -> str:
    """Remove periodicity words from a title."""
    words = normalize(title).split()
    filtered = [w for w in words if w not in PERIODICITY_WORDS]
    return " ".join(filtered).strip() or normalize(title)


def tokenize(title: str) -> List[str]:
    """Return normalized word tokens."""
    return normalize(title).split()


def preprocess(title: str) -> Dict:
    """
    Full preprocessing pipeline.
    Returns dict with all processed forms of the title.
    """
    return {
        "original":   title,
        "normalized": normalize(title),
        "stripped":   strip_affixes(title),
        "tokens":     tokenize(title),
    }
