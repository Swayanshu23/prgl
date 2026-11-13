"""
State-wise title monopoly / saturation check.
Flags titles whose key word already dominates a target state's registrations.
"""
from __future__ import annotations
from collections import Counter
from typing import List, Dict

SATURATION_THRESHOLD = 0.28  # 28% of state titles share the word

_STOP = {
    "the", "a", "an", "and", "of", "for", "in", "at", "to", "by",
    "daily", "times", "news", "samachar", "patra", "patrika",
}


def check_state_monopoly(
    tokens: List[str],
    target_state: str,
    existing_titles: List[str],
) -> Dict:
    """
    Check if a key word in the title is already saturated in the target state.
    Falls back gracefully if state data is sparse.
    """
    if not target_state:
        return {"name": "State Monopoly", "status": "pass", "val": "N/A", "issue": None}

    state_key = target_state.lower().strip()

    # Filter existing titles to those mentioning the state (heuristic)
    state_titles = [
        t for t in existing_titles
        if any(word in t.lower() for word in state_key.split())
    ]

    # If too few state-specific titles, skip (not enough signal)
    if len(state_titles) < 5:
        return {
            "name": "State Monopoly",
            "status": "pass",
            "val": f"Insufficient data for {target_state.title()}",
            "issue": None,
        }

    word_counts: Counter = Counter()
    for t in state_titles:
        for w in t.lower().split():
            if w not in _STOP and len(w) > 3:
                word_counts[w] += 1

    total = len(state_titles)
    for tok in tokens:
        if tok in _STOP or len(tok) <= 3:
            continue
        freq = word_counts.get(tok, 0) / total
        if freq >= SATURATION_THRESHOLD:
            return {
                "name": "State Monopoly",
                "status": "fail",
                "val": f'"{tok}" in {freq:.0%} of {state_key} titles',
                "issue": {
                    "type": "state_monopoly",
                    "detail": (
                        f'Word "{tok}" appears in {freq:.0%} of {target_state.title()} '
                        f"registered titles — regional saturation detected"
                    ),
                },
            }

    return {"name": "State Monopoly", "status": "pass", "val": "OK", "issue": None}
