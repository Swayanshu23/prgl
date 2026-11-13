"""
Historical trend scoring.
Estimates approval likelihood from heuristic features:
word rarity, title length, and script diversity.
"""
from __future__ import annotations
from collections import Counter
from typing import List, Dict

_STOP = {
    "the", "a", "an", "of", "and", "for", "in", "at", "to",
    "daily", "times", "news", "samachar", "patra", "patrika",
}


def _word_rarity(tokens: List[str], existing: List[str]) -> float:
    """0–1: how rare are the words vs. the existing DB? Rarer = more unique."""
    counts: Counter = Counter()
    for title in existing:
        for w in title.lower().split():
            if w not in _STOP:
                counts[w] += 1
    total = max(len(existing), 1)
    scores = []
    for tok in tokens:
        if tok in _STOP:
            continue
        freq = counts.get(tok, 0) / total
        scores.append(1.0 - min(freq * 5, 1.0))
    return round(sum(scores) / len(scores), 3) if scores else 0.5


def _length_score(tokens: List[str]) -> float:
    """0–1: 2-4 word titles trend better."""
    n = len(tokens)
    if 2 <= n <= 4:
        return 1.0
    if n == 1:
        return 0.45
    if n == 5:
        return 0.80
    return max(0.3, 1.0 - (n - 4) * 0.15)


def compute_trend_score(tokens: List[str], existing: List[str]) -> Dict:
    """
    Returns {"boost": int (-15 to +15), "trend_score": int (0-100), "features": dict}
    """
    rarity  = _word_rarity(tokens, existing)
    length  = _length_score(tokens)
    # Script diversity bonus: mixed Indic+Latin tends to be more distinctive
    has_indic = any(any(ord(c) > 127 for c in t) for t in tokens)
    diversity = 0.85 if has_indic else 0.60

    composite = rarity * 0.55 + length * 0.35 + diversity * 0.10
    boost = round((composite - 0.5) * 30)

    return {
        "boost": boost,
        "trend_score": round(composite * 100),
        "features": {
            "word_rarity":     round(rarity * 100),
            "length_score":    round(length * 100),
            "script_diversity": round(diversity * 100),
        },
    }
