"""
Phonetic matching module: Soundex, Metaphone, NYSIIS via jellyfish.
"""
import jellyfish
from pipeline.preprocessor import normalize


def soundex(word: str) -> str:
    try:
        return jellyfish.soundex(word.upper())
    except Exception:
        return "0000"


def metaphone(word: str) -> str:
    try:
        return jellyfish.metaphone(word.upper())
    except Exception:
        return ""


def nysiis(word: str) -> str:
    try:
        return jellyfish.nysiis(word.upper())
    except Exception:
        return ""


def phonetic_score(word1: str, word2: str) -> float:
    """
    Compare two words using Soundex, Metaphone, and NYSIIS.
    Returns average match score (0.0 – 1.0).
    """
    w1, w2 = word1.strip().upper(), word2.strip().upper()
    if not w1 or not w2:
        return 0.0

    scores = []

    # Soundex
    s1, s2 = soundex(w1), soundex(w2)
    scores.append(1.0 if s1 == s2 else (0.5 if s1[0] == s2[0] else 0.0))

    # Metaphone
    m1, m2 = metaphone(w1), metaphone(w2)
    if m1 and m2:
        scores.append(1.0 if m1 == m2 else (0.5 if m1[:2] == m2[:2] else 0.0))

    # NYSIIS
    n1, n2 = nysiis(w1), nysiis(w2)
    if n1 and n2:
        scores.append(1.0 if n1 == n2 else (0.5 if n1[:2] == n2[:2] else 0.0))

    return sum(scores) / len(scores) if scores else 0.0


def phonetic_match(title1: str, title2: str, threshold: float = 0.67) -> bool:
    """
    Returns True if the first words of two titles are phonetically similar
    above the given threshold.
    """
    words1 = normalize(title1).split()
    words2 = normalize(title2).split()
    if not words1 or not words2:
        return False
    return phonetic_score(words1[0], words2[0]) >= threshold
