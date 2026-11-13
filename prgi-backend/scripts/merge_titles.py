"""
Merge 'News Papers in India.csv' into data/titles.csv, then rebuild FAISS index.

Usage (from prgi-backend/ directory):
    python scripts/merge_titles.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT        = Path(__file__).parent.parent
TITLES_CSV  = ROOT / "data" / "titles.csv"
SOURCE_CSV  = Path(r"C:\Users\secha\Downloads\News Papers in India.csv")


def merge():
    # ── Load existing titles ───────────────────────────────────────────────────
    existing = pd.read_csv(TITLES_CSV)
    existing_titles = set(existing.iloc[:, 0].dropna().astype(str).str.strip())
    print(f"[INFO] Existing titles : {len(existing_titles):,}")

    # ── Load new CSV ───────────────────────────────────────────────────────────
    df_new = pd.read_csv(SOURCE_CSV)
    new_titles = (
        df_new["Name"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
    print(f"[INFO] Titles in source: {len(new_titles):,}")

    # ── Deduplicate (case-insensitive) ─────────────────────────────────────────
    seen_lower = {t.lower() for t in existing_titles}
    added = [t for t in new_titles if t.lower() not in seen_lower]
    print(f"[INFO] New (not duplicate): {len(added):,}")

    # ── Append & save ─────────────────────────────────────────────────────────
    all_titles = sorted(existing_titles | set(added))
    out = pd.DataFrame({"title": all_titles})
    out.to_csv(TITLES_CSV, index=False)
    print(f"[OK] titles.csv updated: {len(all_titles):,} total titles")
    return len(all_titles)


if __name__ == "__main__":
    merge()

    # ── Rebuild FAISS index immediately ───────────────────────────────────────
    print("\n[INFO] Rebuilding FAISS index ...")
    from scripts.build_index import build_index
    build_index()
