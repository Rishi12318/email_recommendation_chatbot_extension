# app/services/build_rag_index.py
"""
Builds a FAISS IndexFlatIP (cosine similarity) from cleaned email data.

Key design decisions:
  - All embeddings are L2-normalised BEFORE being added to the index.
    IndexFlatIP on unit vectors == cosine similarity. Without normalisation
    it's a plain dot-product, which gives wrong ranking (longer texts win).
  - Embeddings are generated in batches to avoid OOM on large datasets.
  - A manifest file (models/index_meta.json) is saved alongside the index
    so rag.py can do a quick sanity-check at load time.
"""

import json
import os
import sys

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────

TRAIN_CSV   = "data/train_cleaned.csv"
VAL_CSV     = "data/test_cleaned.csv"
TEXT_COL    = "cleaned_text"          # column that holds the email body
MODELS_DIR  = "models"
INDEX_PATH  = f"{MODELS_DIR}/email_index.faiss"
EMAILS_PATH = f"{MODELS_DIR}/emails.json"
META_PATH   = f"{MODELS_DIR}/index_meta.json"

EMBED_MODEL   = "all-MiniLM-L6-v2"
BATCH_SIZE    = 256   # reduce if you hit OOM; increase for speed on GPU


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_emails() -> list[str]:
    """
    Load train + val CSVs, validate the text column exists,
    drop empty rows, and return a flat list of email strings.
    """
    dfs = []
    for path in (TRAIN_CSV, VAL_CSV):
        if not os.path.exists(path):
            print(f"⚠️  File not found, skipping: {path}")
            continue

        df = pd.read_csv(path)

        if TEXT_COL not in df.columns:
            # Friendly error that tells you exactly what columns ARE present
            print(f"❌  Column '{TEXT_COL}' not found in {path}.")
            print(f"    Available columns: {list(df.columns)}")
            print(f"    Set TEXT_COL at the top of this script to the correct column name.")
            sys.exit(1)

        before = len(df)
        df = df.dropna(subset=[TEXT_COL])
        df = df[df[TEXT_COL].str.strip() != ""]
        after = len(df)

        if before != after:
            print(f"ℹ️  Dropped {before - after} empty rows from {path}")

        dfs.append(df)

    if not dfs:
        print("❌  No CSV files found. Check TRAIN_CSV / VAL_CSV paths.")
        sys.exit(1)

    combined = pd.concat(dfs, ignore_index=True)
    return combined[TEXT_COL].tolist()


def embed_and_normalise(texts: list[str], model: SentenceTransformer) -> np.ndarray:
    """
    Embed `texts` in batches and L2-normalise every vector.

    Why normalise?
      IndexFlatIP computes raw dot products.
      For two unit vectors u, v:  u · v = cos(angle between u and v).
      So normalised dot product == cosine similarity — which is what we want.
      Without normalisation longer emails (bigger embedding norms) rank
      artificially high regardless of relevance.

    Returns float32 array of shape (N, D) where every row has ||row||₂ = 1.
    """
    print(f"  Embedding {len(texts):,} texts in batches of {BATCH_SIZE}…")

    # encode() accepts batch_size directly and shows a progress bar
    vectors = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,   # ← SentenceTransformers built-in L2 norm
    )

    # Double-check normalisation (floating-point may drift slightly)
    norms = np.linalg.norm(vectors, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-4):
        # Fallback: manual normalisation
        print("  Re-normalising (SentenceTransformer drift detected)…")
        norms = np.where(norms == 0, 1.0, norms)
        vectors = vectors / norms[:, np.newaxis]

    return vectors.astype("float32")


# ── Main build function ───────────────────────────────────────────────────────

def build_rag_index() -> None:
    """
    Full pipeline:
      1. Load emails from CSV files
      2. Embed + L2-normalise with SentenceTransformer
      3. Build FAISS IndexFlatIP
      4. Save index, email texts, and a metadata manifest
      5. Verify the saved index loads correctly and matches expected count
    """

    # ── Step 1: Load data ─────────────────────────────────────────────────
    print("\n[1/5] Loading email data…")
    email_texts = load_emails()
    print(f"      Total emails to index: {len(email_texts):,}")

    # ── Step 2: Generate embeddings ───────────────────────────────────────
    print(f"\n[2/5] Loading embedding model '{EMBED_MODEL}'…")
    model = SentenceTransformer(EMBED_MODEL)

    print("\n[3/5] Generating L2-normalised embeddings…")
    embeddings = embed_and_normalise(email_texts, model)

    dimension = embeddings.shape[1]
    print(f"      Embedding dimension : {dimension}")
    print(f"      Matrix shape        : {embeddings.shape}")

    # Quick sanity-check — norms should all be ~1.0
    sample_norms = np.linalg.norm(embeddings[:5], axis=1)
    print(f"      Sample norms (first 5): {sample_norms.round(5).tolist()}")

    # ── Step 3: Build FAISS index ─────────────────────────────────────────
    print("\n[4/5] Building FAISS IndexFlatIP…")
    index = faiss.IndexFlatIP(dimension)   # Inner Product on unit vecs == cosine
    index.add(embeddings)                  # adds all rows at once (fast in-RAM op)
    print(f"      Vectors in index: {index.ntotal:,}")

    # ── Step 4: Save everything ───────────────────────────────────────────
    print(f"\n[5/5] Saving to '{MODELS_DIR}/'…")
    os.makedirs(MODELS_DIR, exist_ok=True)

    faiss.write_index(index, INDEX_PATH)
    print(f"      ✅ FAISS index  → {INDEX_PATH}")

    with open(EMAILS_PATH, "w", encoding="utf-8") as f:
        json.dump(email_texts, f, ensure_ascii=False, indent=2)
    print(f"      ✅ Email texts  → {EMAILS_PATH}")

    # Save a small manifest so rag.py can verify at load time
    meta = {
        "num_emails"  : len(email_texts),
        "dimension"   : int(dimension),
        "index_type"  : "IndexFlatIP",
        "embed_model" : EMBED_MODEL,
        "normalised"  : True,
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"      ✅ Metadata     → {META_PATH}")

    # ── Step 5: Verification round-trip ──────────────────────────────────
    print("\nVerifying saved index…")
    verify_index = faiss.read_index(INDEX_PATH)
    assert verify_index.ntotal == len(email_texts), (
        f"Mismatch: index has {verify_index.ntotal} vectors "
        f"but emails.json has {len(email_texts)} entries"
    )

    # Quick search: first email should score ~1.0 against itself
    test_vec = embeddings[0:1]
    distances, indices = verify_index.search(test_vec, k=1)
    self_score = float(distances[0][0])
    print(f"  Self-similarity score for email[0]: {self_score:.6f}  (expected ≈ 1.0)")
    if abs(self_score - 1.0) > 0.01:
        print(f"  ⚠️  Self-score deviated from 1.0 — check normalisation.")

    print(f"\n🎉 RAG index built successfully! {len(email_texts):,} emails indexed.\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_rag_index()