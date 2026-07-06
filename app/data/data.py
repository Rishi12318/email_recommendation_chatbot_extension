# app/data/data.py
"""
Builds the final training data for the email-recommendation RAG chatbot by
combining THREE sources, since no single dataset covers all 8 categories:

    1. Enron Email Corpus (real, raw, unlabeled)        -> from_work
    2. jason23322/high-accuracy-email-classifier (real)  -> news, otp, other
    3. Synthetic templates (no labeled dataset exists)    -> deadline,
                                                              interview_call,
                                                              confirmation_email,
                                                              expired_email

Output: data/train.csv, data/val.csv with columns:
    text, label, sender, subject, date
"""

import os
import re
import random
from datetime import datetime, timedelta

import pandas as pd
from datasets import load_dataset
from huggingface_hub import login
from dotenv import load_dotenv

load_dotenv()

# ── auth ──────────────────────────────────────────────────────────────────────
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN environment variable not set.\n"
        'PowerShell: $env:HF_TOKEN="hf_your_token_here"'
    )
login(token=HF_TOKEN)

OUT_DIR      = "data"
VAL_FRACTION = 0.15
SEED         = 42
DATE_FORMAT  = "%Y-%m-%d"

CATEGORIES = [
    "deadline",
    "interview_call",
    "from_work",
    "news",
    "confirmation_email",
    "otp",
    "expired_email",
    "other",
]

# Caps so no single source dominates the final dataset
ENRON_CAP       = 1800   # from_work
SYNTHETIC_COUNT = 900    # per synthetic category (4 categories)

random.seed(SEED)


# ════════════════════════════════════════════════════════════════════════════
# 1. ENRON CORPUS -> from_work
# ════════════════════════════════════════════════════════════════════════════
def load_enron_from_work(n: int, today: datetime) -> pd.DataFrame:
    print(f"Loading Enron corpus for 'from_work' ({n} samples)...")
    ds = load_dataset("corbt/enron-emails", split="train")
    df = ds.to_pandas()

    # Different mirrors of this dataset use different column names —
    # handle the common variants defensively.
    text_col = next((c for c in ["text", "body", "message", "content"] if c in df.columns), None)
    if text_col is None:
        raise ValueError(f"Couldn't find an email-body column in Enron dataset: {list(df.columns)}")

    subject_col = next((c for c in ["subject", "Subject"] if c in df.columns), None)
    sender_col  = next((c for c in ["sender", "from", "From"] if c in df.columns), None)
    date_col    = next((c for c in ["date", "Date"] if c in df.columns), None)

    df = df.dropna(subset=[text_col]).sample(
        n=min(n, len(df)), random_state=SEED
    ).reset_index(drop=True)

    rows = []
    for i, row in df.iterrows():
        body = str(row[text_col]).strip()
        if not body:
            continue

        subject = str(row[subject_col]).strip() if subject_col and pd.notna(row.get(subject_col)) else "(no subject)"
        sender  = str(row[sender_col]).strip()  if sender_col  and pd.notna(row.get(sender_col))  else f"colleague{i % 200}@enron-corp.com"

        if date_col and pd.notna(row.get(date_col)):
            try:
                date_str = pd.to_datetime(row[date_col]).strftime(DATE_FORMAT)
            except Exception:
                date_str = (today - timedelta(days=random.randint(30, 720))).strftime(DATE_FORMAT)
        else:
            # Enron mail is historical -> push dates well into the past
            date_str = (today - timedelta(days=random.randint(30, 720))).strftime(DATE_FORMAT)

        rows.append({
            "text": body[:1000],   # cap length, some Enron threads are huge
            "label": CATEGORIES.index("from_work"),
            "sender": sender,
            "subject": subject,
            "date": date_str,
        })

    return pd.DataFrame(rows)


# ════════════════════════════════════════════════════════════════════════════
# 2. jason23322 dataset -> news, otp, other
# ════════════════════════════════════════════════════════════════════════════
CATEGORY_MAP = {
    "promotions":   "news",
    "social_media": "news",
    "forum":        "other",
    "updates":      "news",
    "verify_code":  "otp",
    "spam":         "other",
}

SENDER_RE  = re.compile(r"from\s*:\s*([^\n|]+)", re.IGNORECASE)
SUBJECT_RE = re.compile(r"subject\s*:\s*([^\n|]+)", re.IGNORECASE)
DATE_RE    = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
FALLBACK_DOMAINS = ["promo-mail.com", "updates.io", "notify.net"]


def extract_or_synthesize_meta(text: str, idx: int, today: datetime) -> dict:
    text = text or ""
    sender_match  = SENDER_RE.search(text)
    subject_match = SUBJECT_RE.search(text)
    date_match    = DATE_RE.search(text)

    sender  = sender_match.group(1).strip()  if sender_match  else f"sender{idx % 500}@{FALLBACK_DOMAINS[idx % len(FALLBACK_DOMAINS)]}"
    subject = subject_match.group(1).strip() if subject_match else (text.strip().split("\n")[0][:60] or "No subject")

    if date_match:
        date_str = date_match.group(1)
    else:
        offset_days = (idx % 61) - 30
        date_str = (today + timedelta(days=offset_days)).strftime(DATE_FORMAT)

    return {"sender": sender, "subject": subject, "date": date_str}


def load_jason_subset(today: datetime) -> pd.DataFrame:
    print("Loading jason23322 dataset for news/otp/other...")
    ds = load_dataset("jason23322/high-accuracy-email-classifier")
    df = ds["train"].to_pandas()

    df["mapped_category"] = df["category"].apply(lambda c: CATEGORY_MAP.get(str(c).strip().lower(), None))
    df = df.dropna(subset=["mapped_category"]).reset_index(drop=True)
    df["label"] = df["mapped_category"].apply(CATEGORIES.index)

    extras = [extract_or_synthesize_meta(t, i, today) for i, t in enumerate(df["text"].tolist())]
    extras_df = pd.DataFrame(extras)

    out = pd.concat(
        [df[["text", "label"]].reset_index(drop=True), extras_df.reset_index(drop=True)],
        axis=1,
    )
    return out[["text", "label", "sender", "subject", "date"]]


# ════════════════════════════════════════════════════════════════════════════
# 3. SYNTHETIC TEMPLATES -> deadline, interview_call, confirmation_email, expired_email
# ════════════════════════════════════════════════════════════════════════════
FIRST_NAMES   = ["Alex", "Priya", "Daniel", "Sara", "Wei", "Liam", "Anika", "Omar", "Grace", "Noah"]
COMPANIES     = ["Nexora", "Brightfield", "Veltrix", "Skyline Labs", "OrionTech", "Cascade Co", "Lumen Group", "ApexWorks"]
PLATFORMS     = ["Coursera", "Udemy", "edX", "TestPortal", "HackerRank", "AssessPro", "ExamCentral"]
SHOPS         = ["Amazon", "Flipkart", "BestBuy", "Etsy", "Myntra", "Walmart"]


def rand_date_str(today: datetime, lo: int, hi: int) -> str:
    """lo/hi are day offsets relative to today (can be negative)."""
    offset = random.randint(lo, hi)
    return (today + timedelta(days=offset)).strftime(DATE_FORMAT)


def gen_deadline(today: datetime) -> dict:
    name = random.choice(FIRST_NAMES)
    platform = random.choice(PLATFORMS)
    days_left = random.randint(0, 10)  # upcoming or today
    due_date = rand_date_str(today, days_left, days_left)
    subject = random.choice([
        f"Reminder: Your assessment is due on {due_date}",
        f"Action required: Submit your assignment by {due_date}",
        f"Deadline approaching: {platform} assessment closes {due_date}",
    ])
    body = (
        f"Hi {name},\n\n"
        f"This is a reminder that your assessment on {platform} must be completed "
        f"and submitted by {due_date}. Late submissions will not be accepted.\n\n"
        f"Please log in and finish all sections before the deadline.\n\nRegards,\n{platform} Team"
    )
    return {
        "text": body, "subject": subject,
        "sender": f"noreply@{platform.lower().replace(' ', '')}.com",
        "date": due_date,
    }


def gen_interview_call(today: datetime) -> dict:
    name = random.choice(FIRST_NAMES)
    company = random.choice(COMPANIES)
    days_ahead = random.randint(1, 14)
    interview_date = rand_date_str(today, days_ahead, days_ahead)
    subject = random.choice([
        f"Interview Invitation - {company}",
        f"Your interview with {company} is scheduled",
        f"Next round: {company} interview confirmation",
    ])
    body = (
        f"Dear {name},\n\n"
        f"Congratulations! We would like to invite you to interview for the position "
        f"you applied for at {company}. Your interview is scheduled for {interview_date}.\n\n"
        f"Please confirm your availability at your earliest convenience.\n\nBest regards,\nHR Team, {company}"
    )
    return {
        "text": body, "subject": subject,
        "sender": f"hr@{company.lower().replace(' ', '')}.com",
        "date": interview_date,
    }


def gen_confirmation_email(today: datetime) -> dict:
    name = random.choice(FIRST_NAMES)
    shop = random.choice(SHOPS)
    order_id = random.randint(100000, 999999)
    order_date = rand_date_str(today, -15, 0)
    subject = f"Order Confirmation #{order_id} - {shop}"
    body = (
        f"Hi {name},\n\n"
        f"Thank you for your order! Your order #{order_id} placed on {order_date} "
        f"has been confirmed and is being processed.\n\n"
        f"You will receive a shipping notification soon.\n\nThanks for shopping with {shop}!"
    )
    return {
        "text": body, "subject": subject,
        "sender": f"orders@{shop.lower()}.com",
        "date": order_date,
    }


def gen_expired_email(today: datetime) -> dict:
    name = random.choice(FIRST_NAMES)
    platform = random.choice(PLATFORMS + SHOPS)
    days_past = random.randint(5, 90)
    past_date = rand_date_str(today, -days_past, -days_past)
    subject = random.choice([
        f"[Expired] Your offer from {platform} has ended",
        f"This deadline has passed - {platform}",
        f"Final notice (expired): {platform} assessment window closed",
    ])
    body = (
        f"Hi {name},\n\n"
        f"This was sent on {past_date}. The window for this action has now closed "
        f"and this email is no longer actionable.\n\nRegards,\n{platform} Team"
    )
    return {
        "text": body, "subject": subject,
        "sender": f"noreply@{platform.lower().replace(' ', '')}.com",
        "date": past_date,
    }


SYNTH_GENERATORS = {
    "deadline":           gen_deadline,
    "interview_call":     gen_interview_call,
    "confirmation_email": gen_confirmation_email,
    "expired_email":      gen_expired_email,
}


def build_synthetic(n_per_class: int, today: datetime) -> pd.DataFrame:
    print(f"Generating {n_per_class} synthetic examples each for: {list(SYNTH_GENERATORS.keys())}")
    rows = []
    for category, generator in SYNTH_GENERATORS.items():
        for _ in range(n_per_class):
            item = generator(today)
            item["label"] = CATEGORIES.index(category)
            rows.append(item)
    return pd.DataFrame(rows)[["text", "label", "sender", "subject", "date"]]


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def load_and_prepare():
    today = datetime.now()
    print(f"Today's date: {today.strftime(DATE_FORMAT)}\n")

    enron_df     = load_enron_from_work(ENRON_CAP, today)
    jason_df     = load_jason_subset(today)
    synthetic_df = build_synthetic(SYNTHETIC_COUNT, today)

    full_df = pd.concat([enron_df, jason_df, synthetic_df], ignore_index=True)
    full_df = full_df.sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffle

    split_idx = int(len(full_df) * (1 - VAL_FRACTION))
    train_df = full_df.iloc[:split_idx].reset_index(drop=True)
    val_df   = full_df.iloc[split_idx:].reset_index(drop=True)

    os.makedirs(OUT_DIR, exist_ok=True)
    train_df.to_csv(f"{OUT_DIR}/train.csv", index=False)
    val_df.to_csv(f"{OUT_DIR}/val.csv", index=False)

    print(f"\nTrain size: {len(train_df)}")
    print(f"Val size:   {len(val_df)}")
    print("\nFinal label distribution (train):")
    print(train_df["label"].map(lambda i: CATEGORIES[i]).value_counts().to_string())

    print("\nSample row:")
    print(train_df.iloc[0].to_dict())

    return train_df, val_df


if __name__ == "__main__":
    load_and_prepare()