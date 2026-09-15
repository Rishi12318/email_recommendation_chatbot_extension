# app/evaluation/evaluation.py
"""
Runnable evaluation script for the email classifier.

Usage:
    python -m app.evaluation.evaluation
    python -m app.evaluation.evaluation --data data/val.csv --top-k 2
"""

import argparse
import os
import sys
import json

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

CATEGORIES = [
    "deadline",
    "interview_call",
    "news",
    "confirmation_email",
    "otp",
    "expired_email",
    "other",
]

DATA_LABEL_MAP = {
    0: "deadline",
    1: "interview_call",
    2: "other",           # from_work -> other
    3: "news",
    4: "confirmation_email",
    5: "otp",
    6: "expired_email",
    7: "other",
}

MODEL_DIR = os.path.join(ROOT, "models", "email_classifier")
DATA_PATH = os.path.join(ROOT, "data", "val.csv")
PLOTS_DIR = os.path.join(ROOT, "app", "evaluation", "plots")


def load_model():
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_DIR)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    return tokenizer, model, device


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["label"] = df["label"].apply(lambda x: CATEGORIES.index(DATA_LABEL_MAP[x]))
    return df


def predict_batch(texts, tokenizer, model, device, batch_size=32):
    all_preds = []
    all_probs = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        inputs = tokenizer(
            batch,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            preds = torch.argmax(probs, dim=-1)
        all_preds.extend(preds.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())

    return np.array(all_preds), np.array(all_probs)


def top_k_accuracy(probs: np.ndarray, labels: np.ndarray, k: int = 2) -> float:
    top_k = np.argsort(probs, axis=1)[:, -k:]
    hits = np.array([labels[i] in top_k[i] for i in range(len(labels))])
    return float(hits.mean())


def save_confusion_matrix(y_true, y_pred, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        cm = confusion_matrix(y_true, y_pred, labels=list(range(len(CATEGORIES))))
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
        ax.set(
            xticks=np.arange(len(CATEGORIES)),
            yticks=np.arange(len(CATEGORIES)),
            xticklabels=CATEGORIES,
            yticklabels=CATEGORIES,
            title="Confusion Matrix",
            ylabel="True label",
            xlabel="Predicted label",
        )
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        thresh = cm.max() / 2.0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(
                    j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                )
        fig.colorbar(im)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "confusion_matrix.png"), dpi=150)
        plt.close()
        print(f"Confusion matrix saved to: {out_dir}/confusion_matrix.png")
    except ImportError:
        print("[WARN] matplotlib not installed, skipping confusion matrix plot")


def save_per_class_chart(report_dict, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        metrics = ["precision", "recall", "f1-score"]
        x = np.arange(len(CATEGORIES))
        width = 0.25

        fig, ax = plt.subplots(figsize=(12, 6))
        for i, metric in enumerate(metrics):
            values = [report_dict[c][metric] for c in CATEGORIES if c in report_dict]
            ax.bar(x + i * width, values, width, label=metric)

        ax.set_ylabel("Score")
        ax.set_title("Per-Class Metrics")
        ax.set_xticks(x + width)
        ax.set_xticklabels(CATEGORIES, rotation=45, ha="right")
        ax.legend()
        ax.set_ylim(0, 1.1)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "per_class_metrics.png"), dpi=150)
        plt.close()
        print(f"Per-class metrics chart saved to: {out_dir}/per_class_metrics.png")
    except ImportError:
        print("[WARN] matplotlib not installed, skipping per-class chart")


def main():
    parser = argparse.ArgumentParser(description="Evaluate email classifier")
    parser.add_argument("--data", default=DATA_PATH, help="Path to validation CSV")
    parser.add_argument("--model", default=MODEL_DIR, help="Path to trained model")
    parser.add_argument("--top-k", type=int, default=2, help="Top-k accuracy")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    args = parser.parse_args()

    print("=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    print(f"\nLoading model from {args.model}...")
    tokenizer, model, device = load_model()

    print(f"Loading data from {args.data}...")
    df = load_data(args.data)
    texts = df["text"].astype(str).tolist()
    labels = df["label"].values

    print(f"Running predictions on {len(texts)} samples...")
    preds, probs = predict_batch(texts, tokenizer, model, device, args.batch_size)

    acc = accuracy_score(labels, preds)
    p_macro = precision_score(labels, preds, average="macro", zero_division=0)
    p_weighted = precision_score(labels, preds, average="weighted", zero_division=0)
    r_macro = recall_score(labels, preds, average="macro", zero_division=0)
    r_weighted = recall_score(labels, preds, average="weighted", zero_division=0)
    f1_macro = f1_score(labels, preds, average="macro", zero_division=0)
    f1_weighted = f1_score(labels, preds, average="weighted", zero_division=0)

    try:
        roc_auc = roc_auc_score(labels, probs, multi_class="ovr", average="macro")
    except ValueError:
        roc_auc = 0.0

    top_k = top_k_accuracy(probs, labels, k=args.top_k)

    print(f"\n{'Metric':<40} {'Value':>10}")
    print("-" * 52)
    print(f"{'Accuracy':<40} {acc:>10.4f}")
    print(f"{'Precision (macro)':<40} {p_macro:>10.4f}")
    print(f"{'Precision (weighted)':<40} {p_weighted:>10.4f}")
    print(f"{'Recall (macro)':<40} {r_macro:>10.4f}")
    print(f"{'Recall (weighted)':<40} {r_weighted:>10.4f}")
    print(f"{'F1 (macro)':<40} {f1_macro:>10.4f}")
    print(f"{'F1 (weighted)':<40} {f1_weighted:>10.4f}")
    print(f"{'ROC-AUC (macro OvR)':<40} {roc_auc:>10.4f}")
    print(f"{'Top-' + str(args.top_k) + ' Accuracy':<40} {top_k:>10.4f}")

    report = classification_report(labels, preds, target_names=CATEGORIES, zero_division=0)
    report_dict = classification_report(labels, preds, target_names=CATEGORIES, output_dict=True, zero_division=0)

    print(f"\nPer-class F1 scores:")
    print("-" * 52)
    for cat in CATEGORIES:
        f1 = report_dict[cat]["f1-score"]
        bar = int(f1 * 20)
        print(f"  {cat:<24} {f1:.4f}  {'█' * bar}")

    print(f"\nDetailed Classification Report:")
    print("-" * 52)
    print(report)

    os.makedirs(PLOTS_DIR, exist_ok=True)

    save_confusion_matrix(labels, preds, PLOTS_DIR)
    save_per_class_chart(report_dict, PLOTS_DIR)

    metrics_df = pd.DataFrame([{
        "accuracy": acc,
        "precision_macro": p_macro,
        "precision_weighted": p_weighted,
        "recall_macro": r_macro,
        "recall_weighted": r_weighted,
        "f1_macro": f1_macro,
        "f1_weighted": f1_weighted,
        "roc_auc_macro": roc_auc,
        f"top_{args.top_k}_accuracy": top_k,
    }])
    metrics_df.to_csv(os.path.join(PLOTS_DIR, "metrics.csv"), index=False)
    print(f"Metrics CSV saved to: {PLOTS_DIR}/metrics.csv")

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()
