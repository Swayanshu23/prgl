"""
Fuzzy string similarity: Levenshtein, Jaro-Winkler, n-gram via rapidfuzz.
"""
from rapidfuzz import fuzz
from typing import List, Dict


def levenshtein_sim(a: str, b: str) -> float:
    """Normalized Levenshtein similarity, 0–100."""
    return fuzz.ratio(a.lower(), b.lower())


def jaro_winkler_sim(a: str, b: str) -> float:
    """Jaro-Winkler similarity, 0–100."""
    return fuzz.WRatio(a.lower(), b.lower())


def ngram_sim(a: str, b: str, n: int = 2) -> float:
    """Character n-gram Jaccard overlap, 0–100."""
    def ngrams(s: str, n: int):
        return set(s[i:i + n] for i in range(len(s) - n + 1))

    ag, bg = ngrams(a.lower(), n), ngrams(b.lower(), n)
    if not ag and not bg:
        return 100.0
    if not ag or not bg:
        return 0.0
    return round(len(ag & bg) / len(ag | bg) * 100, 1)


def combined_fuzzy_score(a: str, b: str) -> float:
    """
    Weighted combination: 40% Levenshtein, 40% Jaro-Winkler, 20% bigram.
    Returns 0–100.
    """
    lev = levenshtein_sim(a, b)
    jw  = jaro_winkler_sim(a, b)
    ng  = ngram_sim(a, b)
    return round(lev * 0.4 + jw * 0.4 + ng * 0.2, 1)


def top_similar(
    query: str,
    candidates: List[str],
    top_k: int = 5,
    min_score: float = 45.0,
) -> List[Dict]:
    """
    Return the top-k most similar titles above min_score.
    Each result: {"title": str, "score": float}
    """
    results = []
    for candidate in candidates:
        score = combined_fuzzy_score(query, candidate)
        if score >= min_score:
            results.append({"title": candidate, "score": score})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
