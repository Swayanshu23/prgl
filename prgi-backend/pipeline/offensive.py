"""
Offensive & sensitive content detection.
Checks for prohibited words in English and major Indian languages.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict

DATA_DIR = Path(__file__).parent.parent / "data"

_DEFAULT_OFFENSIVE = {
    "en":      ["hate", "kill", "murder", "rape", "terrorist", "bastard",
                 "porn", "xxx", "nude", "obscene", "vulgar"],
    "hi":      ["harami", "kutta", "kamina", "saala", "randi", "chutiya"],
    "ta":      ["thevidiya", "otha"],
    "te":      ["dengu", "pooku"],
    "generic": ["terror", "bomb", "mafia", "narcotic", "narco"],
}

_SENSITIVE = [
    "caste", "untouchable", "dalit", "brahmin", "harijan",
    "hindutva", "islamist", "crusade", "infidel",
]


def _load_offensive() -> dict:
    path = DATA_DIR / "offensive.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _DEFAULT_OFFENSIVE


def check_offensive(tokens: List[str], full_title: str) -> Dict:
    """
    Returns fail for offensive words, warn for sensitive (but not banned) words.
    """
    word_lists = _load_offensive()
    all_offensive = [w for lang_words in word_lists.values() for w in lang_words]
    lower_tokens = [t.lower() for t in tokens]
    full_lower = full_title.lower()

    for word in all_offensive:
        if word in lower_tokens or word in full_lower.split():
            return {
                "name": "Offensive Content",
                "status": "fail",
                "val": word.upper(),
                "issue": {
                    "type": "offensive",
                    "detail": f'Title contains offensive/prohibited content: "{word}"',
                },
            }

    for word in _SENSITIVE:
        if word in lower_tokens:
            return {
                "name": "Offensive Content",
                "status": "warn",
                "val": word.upper(),
                "issue": None,
            }

    return {"name": "Offensive Content", "status": "pass", "val": "Clear", "issue": None}
