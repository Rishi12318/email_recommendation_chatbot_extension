# build_pipeline.py
"""
One-shot pipeline runner for the email RAG system.

Runs three steps in sequence:
    Step 1: app/data/data.py          -> data/train.csv, data/val.csv
    Step 2: app/data/preprocess.py    -> data/train_cleaned.csv, data/test_cleaned.csv
    Step 3: app/services/build_rag_index.py -> models/email_index.faiss, models/emails.json

Run from the project root:
    python build_pipeline.py

Optional: skip steps you've already done:
    python build_pipeline.py --skip-data        (skip Step 1 — reuse existing CSVs)
    python build_pipeline.py --skip-preprocess  (skip Steps 1+2 — reuse cleaned CSVs)
"""

import argparse
import os
import sys
import time

import pandas as pd

# ── Make sure project root is on sys.path ─────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Paths ─────────────────────────────────────────────────────────────────────
RAW_TRAIN   = "data/train.csv"
RAW_VAL     = "data/val.csv"
CLEAN_TRAIN = "data/train_cleaned.csv"
CLEAN_TEST  = "data/test_cleaned.csv"    # build_rag_index.py expects this name
INDEX_PATH  = "models/email_index.faiss"
EMAILS_PATH = "models/emails.json"


def banner(msg: str) -> None:
    width = 68
    print("\n" + "=" * width)
    print(f"  {msg}")
    print("=" * width)


def elapsed(start: float) -> str:
    secs = time.time() - start
    return f"{secs:.1f}s" if secs < 60 else f"{secs/60:.1f}min"


# ════════════════════════════════════════════════════════════════════════════
# Step 1 — Generate raw data
# ════════════════════════════════════════════════════════════════════════════
def step1_generate_data() -> None:
    banner("STEP 1 / 3 — Generating raw email data (data.py)")
    t = time.time()

    # Import and run inside this process so we share the same venv
    from app.data.data import load_and_prepare
    train_df, val_df = load_and_prepare()

    print(f"\n✅  Step 1 done in {elapsed(t)}")
    print(f"    data/train.csv : {len(train_df):,} rows")
    print(f"    data/val.csv   : {len(val_df):,} rows")


# ════════════════════════════════════════════════════════════════════════════
# Step 2 — Preprocess / clean
# ════════════════════════════════════════════════════════════════════════════
def step2_preprocess() -> None:
    banner("STEP 2 / 3 — Cleaning email text (preprocess.py)")
    t = time.time()

    # Validate inputs
    for path in (RAW_TRAIN, RAW_VAL):
        if not os.path.exists(path):
            print(f"❌  Required file not found: {path}")
            print("    Run Step 1 first (or remove --skip-data).")
            sys.exit(1)

    from app.data.preprocesses import preprocess_for_rag

    train_df = pd.read_csv(RAW_TRAIN)
    val_df   = pd.read_csv(RAW_VAL)

    print(f"  Loaded train: {len(train_df):,} rows | val: {len(val_df):,} rows")

    # preprocess_for_rag expects a 'text' column — verify
    for name, df in (("train", train_df), ("val", val_df)):
        if "text" not in df.columns:
            print(f"❌  'text' column missing from {name}.csv")
            print(f"    Available columns: {list(df.columns)}")
            sys.exit(1)

    train_clean = preprocess_for_rag(train_df, text_column="text")
    val_clean   = preprocess_for_rag(val_df,   text_column="text")

    # Drop rows where cleaning produced an empty string
    before_t, before_v = len(train_clean), len(val_clean)
    train_clean = train_clean[train_clean["cleaned_text"].str.strip().str.len() > 20]
    val_clean   = val_clean[val_clean["cleaned_text"].str.strip().str.len() > 20]
    dropped = (before_t - len(train_clean)) + (before_v - len(val_clean))
    if dropped:
        print(f"  ℹ️   Dropped {dropped} rows with <20 chars after cleaning")

    os.makedirs("data", exist_ok=True)
    train_clean.to_csv(CLEAN_TRAIN, index=False)
    val_clean.to_csv(CLEAN_TEST,   index=False)   # named test_cleaned to match build_rag_index

    print(f"\n✅  Step 2 done in {elapsed(t)}")
    print(f"    data/train_cleaned.csv : {len(train_clean):,} rows")
    print(f"    data/test_cleaned.csv  : {len(val_clean):,} rows")


# ════════════════════════════════════════════════════════════════════════════
# Step 3 — Build FAISS index
# ════════════════════════════════════════════════════════════════════════════
def step3_build_index() -> None:
    banner("STEP 3 / 3 — Building FAISS RAG index (build_rag_index.py)")
    t = time.time()

    for path in (CLEAN_TRAIN, CLEAN_TEST):
        if not os.path.exists(path):
            print(f"❌  Required file not found: {path}")
            print("    Run Steps 1 and 2 first.")
            sys.exit(1)

    from app.services.build_rag_index import build_rag_index
    build_rag_index()

    print(f"\n✅  Step 3 done in {elapsed(t)}")
    print(f"    models/email_index.faiss : {os.path.getsize(INDEX_PATH) / 1e6:.1f} MB")
    print(f"    models/emails.json       : {os.path.getsize(EMAILS_PATH) / 1e6:.1f} MB")


# ════════════════════════════════════════════════════════════════════════════
# Entry point
# ════════════════════════════════════════════════════════════════════════════
def main() -> None:
    parser = argparse.ArgumentParser(description="Build the email RAG pipeline end-to-end.")
    parser.add_argument(
        "--skip-data",
        action="store_true",
        help="Skip Step 1 (data generation). Reuse existing data/train.csv and data/val.csv.",
    )
    parser.add_argument(
        "--skip-preprocess",
        action="store_true",
        help="Skip Steps 1 and 2 (data + cleaning). Reuse existing cleaned CSVs.",
    )
    args = parser.parse_args()

    total_start = time.time()

    if args.skip_preprocess:
        print("ℹ️  Skipping Steps 1 and 2 — using existing cleaned CSVs.")
        for path in (CLEAN_TRAIN, CLEAN_TEST):
            if not os.path.exists(path):
                print(f"❌  Cleaned CSV not found: {path} — cannot skip preprocessing.")
                sys.exit(1)
    elif args.skip_data:
        print("ℹ️  Skipping Step 1 — using existing raw CSVs.")
        for path in (RAW_TRAIN, RAW_VAL):
            if not os.path.exists(path):
                print(f"❌  Raw CSV not found: {path} — cannot skip data generation.")
                sys.exit(1)
        step2_preprocess()
    else:
        step1_generate_data()
        step2_preprocess()

    step3_build_index()

    banner(f"ALL DONE — total time: {elapsed(total_start)}")
    print("  Next step:  python app/services/rag.py")
    print("  Or run:     python app/main.py\n")


if __name__ == "__main__":
    main()