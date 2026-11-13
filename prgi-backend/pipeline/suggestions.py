"""
Title Suggestion Engine.
Generates unique alternative title suggestions for rejected/flagged titles
using synonym substitution and safe prefix/suffix vocabulary pools.
"""
from __future__ import annotations
import random
from typing import List, Dict

_SYNONYMS: Dict[str, List[str]] = {
    "morning":   ["dawn", "prabhat", "bhor", "pratah", "aurora", "aarambh"],
    "evening":   ["sandhya", "dusk", "sham", "twilight", "sayam"],
    "daily":     ["pratidin", "nityam", "rozana", "dainik"],
    "news":      ["khabar", "vartha", "samachar", "sandesh", "tidings"],
    "india":     ["bharat", "hindustan", "rashtra", "desh", "bharatam"],
    "voice":     ["awaaz", "dhwani", "swara", "vani", "echo"],
    "sun":       ["surya", "ravi", "aditya", "bhaskar", "dinkar", "kiran"],
    "world":     ["vishwa", "jagat", "duniya", "global", "sansaar"],
    "light":     ["jyoti", "prakash", "deepak", "ujala", "alo"],
    "people":    ["lok", "jan", "jana", "praja", "janta"],
    "new":       ["nav", "nava", "navin", "nutan", "pratham"],
    "truth":     ["satya", "sach", "satyam", "satta"],
    "times":     ["kaal", "samay", "yug", "yugam"],
    "herald":    ["ghoshna", "udghosh", "banner", "setu"],
    "chronicle": ["itihas", "vritant", "annal"],
    "star":      ["tara", "nakshatra", "sitara", "jyoti"],
    "express":   ["tez", "turanta", "vega"],
    "mirror":    ["darpan", "pratibimba", "aaina"],
    "post":      ["sandesh", "dak", "patr"],
    "journal":   ["patrika", "ank", "pothi"],
    "observer":  ["nirikshak", "darshak"],
    "today":     ["aaj", "abhi", "adyam"],
    "national":  ["rashtriya", "bharatiya", "deshiya"],
    "eastern":   ["purva", "poorvi", "purab"],
    "western":   ["paschim", "pashchimi"],
    "northern":  ["uttar", "uttari"],
    "southern":  ["dakshin", "dakshinam"],
}

_SAFE_PREFIXES = [
    "Nav", "Nava", "Pratham", "Ujwal", "Swachh", "Sreshtha",
    "Agrani", "Pragati", "Vikas", "Samridh", "Vistaar", "Suraj",
    "Shakti", "Teja", "Anand", "Siddhi", "Ujala", "Sparsh",
]

_SAFE_SUFFIXES = [
    "Kiran", "Sandesh", "Darpan", "Patrika", "Vaani", "Setu",
    "Doot", "Vidyut", "Geet", "Sangam", "Saar", "Lok", "Darshan",
]


def _swap_synonym(token: str) -> List[str]:
    return _SYNONYMS.get(token.lower(), [])


def _unique(suggestion: str, existing: List[str], threshold: float = 72.0) -> bool:
    from rapidfuzz import fuzz
    return all(fuzz.ratio(suggestion.lower(), t.lower()) < threshold for t in existing)


def generate_suggestions(
    rejected_title: str,
    tokens: List[str],
    existing_titles: List[str],
    n: int = 5,
) -> List[str]:
    """
    Generate up to n unique alternative title suggestions.
    """
    candidates: List[str] = []

    # Synonym substitution
    for i, tok in enumerate(tokens):
        for syn in _swap_synonym(tok)[:3]:
            variant = " ".join(tokens[:i] + [syn.title()] + tokens[i+1:])
            if variant.lower() != rejected_title.lower():
                candidates.append(variant)

    # Prefix / suffix combos
    core = [t for t in tokens if len(t) > 3]
    if core:
        for _ in range(8):
            word = random.choice(core).title()
            pat = random.choice([
                f"{random.choice(_SAFE_PREFIXES)} {word}",
                f"{word} {random.choice(_SAFE_SUFFIXES)}",
                f"{random.choice(_SAFE_PREFIXES)} {random.choice(_SAFE_SUFFIXES)}",
            ])
            candidates.append(pat)

    # Filter for uniqueness and deduplicate
    seen: set = set()
    result: List[str] = []
    for s in candidates:
        norm = s.lower()
        if norm not in seen and norm != rejected_title.lower() and _unique(s, existing_titles):
            seen.add(norm)
            result.append(s)
        if len(result) >= n:
            break

    # Pad if needed
    for _ in range(n - len(result)):
        fallback = f"{random.choice(_SAFE_PREFIXES)} {random.choice(_SAFE_SUFFIXES)}"
        if fallback.lower() not in seen:
            seen.add(fallback.lower())
            result.append(fallback)

    return result[:n]
