"""
Compliance rules engine.
Checks: disallowed words, periodicity rule, title combination rule.
"""
import json
from pathlib import Path
from typing import List, Dict

DATA_DIR = Path(__file__).parent.parent / "data"

_DEFAULT_DISALLOWED = [
    "police", "crime", "corruption", "cbi", "cid", "army", "navy", "raw", "ib",
    "terror", "bomb", "drug", "mafia", "gang", "murder", "scam", "airforce",
    "military", "defence", "defense", "paramilitary", "nsa", "interpol",
    "smuggling", "trafficking", "narcotics", "naxal", "insurgent", "extremist",
]

PERIODICITY_WORDS = {
    "daily", "weekly", "monthly", "quarterly", "annual", "biweekly",
    "fortnightly", "bi-weekly", "yearly", "pratidin", "saptahik", "masik",
}


def _load_disallowed() -> List[str]:
    path = DATA_DIR / "disallowed.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f).get("words", _DEFAULT_DISALLOWED)
        except Exception:
            pass
    return _DEFAULT_DISALLOWED


def check_disallowed(tokens: List[str]) -> Dict:
    """Fail if any token is a disallowed word."""
    banned = _load_disallowed()
    found  = next((w for w in tokens if w in banned), None)
    if found:
        return {
            "name": "Disallowed Words", "status": "fail", "val": found.upper(),
            "issue": {
                "type": "banned_word",
                "detail": f'Contains disallowed word: "{found.upper()}"',
            },
        }
    return {"name": "Disallowed Words", "status": "pass", "val": "None found", "issue": None}


def check_periodicity(
    tokens: List[str],
    periodicity: str,
    existing_titles: List[str],
) -> Dict:
    """
    Fail if the title is an existing title with a periodicity suffix/prefix added.
    """
    from pipeline.fuzzy import levenshtein_sim
    from pipeline.preprocessor import strip_affixes

    fp = next((w for w in tokens if w in PERIODICITY_WORDS), None)
    if fp or periodicity:
        stripped = " ".join(w for w in tokens if w not in PERIODICITY_WORDS)
        conflict = next(
            (t for t in existing_titles if levenshtein_sim(stripped, strip_affixes(t)) > 75),
            None,
        )
        if conflict:
            return {
                "name": "Periodicity Rule", "status": "fail", "val": fp or periodicity,
                "issue": {
                    "type": "periodicity",
                    "detail": (
                        f'Adding periodicity to existing title "{conflict}" is not allowed'
                    ),
                },
            }
        return {"name": "Periodicity Rule", "status": "pass", "val": "OK", "issue": None}
    return {"name": "Periodicity Rule", "status": "pass", "val": "N/A", "issue": None}


def check_combination(tokens: List[str], existing_titles: List[str]) -> Dict:
    """
    Fail if the title combines 2+ significant words from different existing titles.
    """
    existing_words = {
        w
        for t in existing_titles
        for w in t.lower().split()
        if len(w) > 3
    }
    matched = [w for w in tokens if len(w) > 3 and w in existing_words]
    if len(matched) >= 2:
        word_list = ", ".join(f'"{w}"' for w in matched)
        return {
            "name": "Title Combination", "status": "fail", "val": "+".join(matched),
            "issue": {
                "type": "combination",
                "detail": f"Title combines existing registered words: {word_list}",
            },
        }
    return {"name": "Title Combination", "status": "pass", "val": "Not detected", "issue": None}
