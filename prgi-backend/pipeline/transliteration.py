"""
Transliteration normalizer: collapses Roman-script spelling variants
of Indic words before fuzzy comparison.

Examples:
  "Dainik" / "Daynik" / "Danik"       → "dainik"
  "Prabhat" / "Prabhaat" / "Prabhath" → "prabhat"
  "Samachar" / "Samachaar"            → "samachar"
"""
from __future__ import annotations
import re
from typing import List

# Canonical forms for common Indic words (highest priority)
_CANONICAL: dict = {
    "daynik": "dainik", "danik": "dainik", "daanik": "dainik",
    "dainik": "dainik",
    "prabhaat": "prabhat", "prabhath": "prabhat", "prabhath": "prabhat",
    "samachaar": "samachar", "samacar": "samachar", "samachara": "samachar",
    "hindoostan": "hindustan", "hindostan": "hindustan",
    "bharath": "bharat", "bhaarath": "bharat", "bharatha": "bharat",
    "pratideen": "pratidin", "pratidhin": "pratidin",
    "saptahic": "saptahik", "saptahiq": "saptahik",
    "avaz": "awaaz", "awaz": "awaaz",
    "gyan": "gian", "gyaan": "gian",
    "shri": "sri", "shree": "sri",
    "namaskar": "namaskar", "namascar": "namaskar", "namaskaar": "namaskar",
}

# Substitution rules applied in order (regex, replacement)
_RULES: List[tuple] = [
    (r"aa", "a"), (r"ee", "i"), (r"oo", "u"), (r"ii", "i"), (r"uu", "u"),
    (r"bh", "b"), (r"ph", "f"), (r"gh", "g"), (r"kh", "k"),
    (r"dh", "d"), (r"th", "t"), (r"jh", "j"), (r"ch", "c"), (r"sh", "s"),
    (r"(?<![aeiou])y(?=[aeiou])", "i"),   # 'y' as vowel (Daynik→Dainik)
    (r"w", "v"),
    (r"q", "k"),
    (r"x", "ks"),
]


def normalize_transliteration(word: str) -> str:
    """Reduce a word to its canonical transliteration form."""
    w = word.lower().strip()
    if w in _CANONICAL:
        return _CANONICAL[w]
    for pattern, replacement in _RULES:
        w = re.sub(pattern, replacement, w)
    return w


def normalize_title(title: str) -> str:
    """Apply transliteration normalization to every word in a title."""
    return " ".join(normalize_transliteration(t) for t in title.split())
