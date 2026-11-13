"""
Cross-language duplicate detection.
Maps regional-language words to their English equivalents and checks
whether the title conceptually overlaps with any existing registered title.
"""
from typing import List, Dict, Optional, Tuple

# English concept → list of equivalent native words
CROSS_LANG: Dict[str, List[str]] = {
    "morning": ["prabhat", "subah", "kali", "pori", "bhor"],
    "evening": ["sandhya", "sham", "sayam", "sayankaal"],
    "daily":   ["pratidin", "rozana", "dainik", "pratidina"],
    "news":    ["samachar", "khabar", "vartha", "patrika"],
    "india":   ["bharat", "hindustan", "bharatam"],
    "voice":   ["awaaz", "awaz", "dhwani", "swara"],
    "sun":     ["surya", "ravi", "aditya", "suraj", "aftaab"],
    "world":   ["vishwa", "duniya", "jagat", "sansaar"],
    "light":   ["prakash", "jyoti", "deepak", "alo"],
    "people":  ["jan", "jana", "lok", "praja", "manush"],
    "new":     ["nav", "nava", "naya", "navin"],
    "truth":   ["satya", "sach", "sachchi"],
    "land":    ["bhumi", "bhoomi", "zamin", "desh"],
    "time":    ["kal", "samay", "waqt", "kaal"],
    "power":   ["shakti", "bal", "tej", "urja"],
    "fire":    ["agni", "aag", "jwala"],
    "water":   ["jal", "paani", "neer", "vari"],
    "sky":     ["aakash", "aasman", "nabh", "gagan"],
}

# Reverse map: any word → its English concept
_REVERSE: Dict[str, str] = {}
for _eng, _natives in CROSS_LANG.items():
    _REVERSE[_eng] = _eng
    for _n in _natives:
        _REVERSE[_n] = _eng


def detect_concept(tokens: List[str]) -> Optional[Tuple[str, str]]:
    """
    Return (english_concept, found_word) for the first token that maps
    to a known cross-language concept, or None.
    """
    for word in tokens:
        concept = _REVERSE.get(word)
        if concept:
            return concept, word
    return None


def cross_language_check(tokens: List[str], existing_titles: List[str]) -> Dict:
    """
    Check whether the title's concept (in any language) already exists
    among registered titles.

    Returns a check-result dict with optional "issue" key.
    """
    match = detect_concept(tokens)
    if not match:
        return {
            "name": "Cross-Language", "status": "pass",
            "val": "Checked", "issue": None,
        }

    concept, found_word = match

    for title in existing_titles:
        for tw in title.lower().split():
            if _REVERSE.get(tw) == concept:
                return {
                    "name": "Cross-Language",
                    "status": "fail",
                    "val": f"≈ {title}",
                    "issue": {
                        "type": "cross_lang",
                        "detail": (
                            f'Cross-language similarity: "{found_word}" ≈ '
                            f'"{concept}" — conflicts with existing title "{title}"'
                        ),
                    },
                }

    return {
        "name": "Cross-Language", "status": "pass",
        "val": "No match", "issue": None,
    }
