"""
Language auto-detection for submitted titles.
Uses Unicode script analysis first, then langdetect for Latin-script titles.
"""
from __future__ import annotations
from typing import Tuple

_LANG_LABELS = {
    "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu",  "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada",
    "ml": "Malayalam", "pa": "Punjabi", "ur": "Urdu", "or": "Odia",
    "as": "Assamese", "sa": "Sanskrit", "ne": "Nepali",
}

_SCRIPT_RANGES = [
    (0x0900, 0x097F, "hi"),
    (0x0980, 0x09FF, "bn"),
    (0x0A00, 0x0A7F, "pa"),
    (0x0A80, 0x0AFF, "gu"),
    (0x0B00, 0x0B7F, "or"),
    (0x0B80, 0x0BFF, "ta"),
    (0x0C00, 0x0C7F, "te"),
    (0x0C80, 0x0CFF, "kn"),
    (0x0D00, 0x0D7F, "ml"),
    (0x0600, 0x06FF, "ur"),
]


def _detect_by_script(text: str) -> Tuple[str, float]:
    counts: dict = {}
    for ch in text:
        cp = ord(ch)
        for lo, hi, lang in _SCRIPT_RANGES:
            if lo <= cp <= hi:
                counts[lang] = counts.get(lang, 0) + 1
    if not counts:
        return "en", 0.0
    best = max(counts, key=counts.__getitem__)
    total = sum(counts.values())
    return best, round(counts[best] / total, 2)


def detect_language(text: str) -> dict:
    """
    Detect language of the title.
    Returns {"code", "label", "confidence", "method"}
    """
    code, conf = _detect_by_script(text)
    if conf > 0.5:
        return {
            "code": code,
            "label": _LANG_LABELS.get(code, code.upper()),
            "confidence": conf,
            "method": "script",
        }

    try:
        from langdetect import detect_langs
        results = detect_langs(text)
        if results:
            top = results[0]
            lcode = top.lang.split("-")[0]
            return {
                "code": lcode,
                "label": _LANG_LABELS.get(lcode, lcode.upper()),
                "confidence": round(top.prob, 2),
                "method": "langdetect",
            }
    except Exception:
        pass

    return {"code": "en", "label": "English", "confidence": 0.75, "method": "fallback"}
