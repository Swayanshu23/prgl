"""
Build the FAISS semantic index from titles.csv.

Usage (from prgi-backend/ directory):
    python scripts/build_index.py

Outputs:
    data/faiss.index  — FAISS IndexFlatIP of title embeddings
    data/titles.npy   — numpy array of title strings (aligned to index)
"""
import sys
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import faiss
import numpy as np
import pandas as pd

from pipeline.semantic import embed

DATA_DIR    = Path(__file__).parent.parent / "data"
TITLES_CSV  = DATA_DIR / "titles.csv"
INDEX_OUT   = DATA_DIR / "faiss.index"
TITLES_OUT  = DATA_DIR / "titles.npy"
BATCH_SIZE  = 256


def build_index():
    # ── Load titles ───────────────────────────────────────────────────────────
    if not TITLES_CSV.exists():
        print(f"[ERROR] {TITLES_CSV} not found. Add your titles.csv first.")
        sys.exit(1)

    df = pd.read_csv(TITLES_CSV)
    titles: list = df.iloc[:, 0].dropna().astype(str).tolist()
    print(f"[INFO] Loaded {len(titles):,} titles")

    # ── Build embeddings in batches ───────────────────────────────────────────
    print(f"[INFO] Encoding with model 'paraphrase-multilingual-MiniLM-L12-v2' ...")
    all_embeddings = []
    for start in range(0, len(titles), BATCH_SIZE):
        batch = titles[start:start + BATCH_SIZE]
        vecs  = embed(batch)
        all_embeddings.append(vecs)
        pct = min(100, round((start + len(batch)) / len(titles) * 100))
        print(f"  {pct:3d}%  ({start + len(batch):,} / {len(titles):,})", end="\r")

    embeddings = np.vstack(all_embeddings).astype("float32")
    print(f"\n[INFO] Embeddings shape: {embeddings.shape}")

    # ── Build FAISS index (Inner Product = cosine sim for normalised vecs) ────
    dim   = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"[INFO] FAISS index contains {index.ntotal:,} vectors")

    # ── Save ──────────────────────────────────────────────────────────────────
    faiss.write_index(index, str(INDEX_OUT))
    np.save(str(TITLES_OUT), np.array(titles, dtype=object))
    print(f"[OK] Index saved  → {INDEX_OUT}")
    print(f"[OK] Titles saved → {TITLES_OUT}")


if __name__ == "__main__":
    build_index()
