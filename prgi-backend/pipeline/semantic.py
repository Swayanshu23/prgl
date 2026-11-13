"""
Semantic similarity: multilingual sentence-transformers + FAISS index.

Usage:
  1. Build the index first:  python scripts/build_index.py
  2. Then semantic_search() will use the pre-built FAISS index.

If the index is not found, semantic_search() returns [] gracefully
so the rest of the pipeline continues without semantic scores.
"""
from __future__ import annotations

import logging
import numpy as np
from pathlib import Path
from typing import List, Dict

# Suppress the benign "embeddings.position_ids UNEXPECTED" load report that
# sentence-transformers 5.x emits when a checkpoint pre-dates the position_ids
# buffer.  The model loads and operates correctly regardless.
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

DATA_DIR   = Path(__file__).parent.parent / "data"
INDEX_PATH = DATA_DIR / "faiss.index"
TITLES_PATH = DATA_DIR / "titles.npy"

# Lazy-loaded singletons
_model = None
_index = None
_titles: List[str] = []

# Multilingual model – good balance of speed vs. quality for a hackathon demo
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _get_index():
    global _index, _titles
    if _index is None:
        import faiss
        if not INDEX_PATH.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {INDEX_PATH}.\n"
                "Run:  python scripts/build_index.py"
            )
        _index  = faiss.read_index(str(INDEX_PATH))
        _titles = np.load(str(TITLES_PATH), allow_pickle=True).tolist()
    return _index, _titles


def embed(texts: List[str]) -> np.ndarray:
    """Encode a list of strings into normalized embeddings."""
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def semantic_search(query: str, top_k: int = 5) -> List[Dict]:
    """
    Find the top-k semantically similar titles using FAISS.
    Returns list of {"title": str, "score": float} sorted by score desc.
    Score is cosine similarity × 100 (0–100 range).
    Falls back to [] if the index has not been built yet.
    """
    try:
        index, titles = _get_index()
        model         = _get_model()
        q_vec = model.encode([query], normalize_embeddings=True)
        distances, indices = index.search(q_vec, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(titles):
                continue
            score = max(0.0, round(float(dist) * 100, 1))
            results.append({"title": titles[idx], "score": score})
        return results
    except FileNotFoundError:
        return []   # index not built – graceful degradation
    except Exception:
        return []
