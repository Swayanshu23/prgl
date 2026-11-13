"""
Abbreviation & Acronym expansion.
'HT' → 'Hindustan Times', 'TOI' → 'Times of India', etc.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Optional

DATA_DIR = Path(__file__).parent.parent / "data"

_DEFAULT_ACRONYMS: Dict[str, str] = {
    "HT":  "Hindustan Times",    "TOI": "Times of India",
    "IE":  "Indian Express",     "ET":  "Economic Times",
    "BS":  "Business Standard",  "FE":  "Financial Express",
    "BT":  "Business Today",     "TH":  "The Hindu",
    "TT":  "The Tribune",        "DB":  "Dainik Bhaskar",
    "DJ":  "Dainik Jagran",      "DN":  "Dainik Navjivan",
    "NS":  "Nav Samachar",       "MH":  "Morning Herald",
    "DH":  "Deccan Herald",      "DC":  "Deccan Chronicle",
    "PTI": "Press Trust of India",
    "ANI": "Asian News International",
    "UNI": "United News of India",
    "NB":  "Nav Bharat",         "HH":  "Hindustan Herald",
}


def _load_acronyms() -> Dict[str, str]:
    path = DATA_DIR / "acronyms.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _DEFAULT_ACRONYMS


def expand_acronym(token: str) -> Optional[str]:
    return _load_acronyms().get(token.upper())


def check_abbreviation(tokens: List[str], existing_titles: List[str]) -> Dict:
    """Check if any token is an acronym that expands to an existing title."""
    from rapidfuzz import fuzz
    acr = _load_acronyms()
    for tok in tokens:
        expanded = acr.get(tok.upper())
        if expanded:
            for title in existing_titles:
                if fuzz.ratio(expanded.lower(), title.lower()) > 70:
                    return {
                        "name": "Acronym Conflict",
                        "status": "fail",
                        "val": f"{tok.upper()} ≈ {expanded}",
                        "issue": {
                            "type": "acronym",
                            "detail": f'Acronym "{tok.upper()}" expands to "{expanded}" — conflicts with "{title}"',
                        },
                    }
    return {"name": "Acronym Conflict", "status": "pass", "val": "No conflict", "issue": None}
