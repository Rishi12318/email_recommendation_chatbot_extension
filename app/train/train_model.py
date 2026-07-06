import os
import sys
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from sklearn.metrics import accuracy_score, f1_score

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
NUM_LABELS = len(CATEGORIES)
MODEL_DIR = os.path.join(ROOT, "models", "email_classifier")

data_label_to_cat = {
    0: "deadline",
    1: "interview_call",
    2: "other",
    3: "news",
    4: "confirmation_email",
    5: "otp",
    6: "expired_email",
    7: "other",
}

def remap_label(old_label):
    return CATEGORIES.index(data_label_to_cat[old_label])

class EmailDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=512):
        self.texts = texts.reset_index(drop=True)
        self.labels = labels.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            str(self.texts[idx]),
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
        }

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = logits.argmax(-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_weighted": f1_score(labels, preds, average="weighted"),
    }

def main():
    print("Loading data...")
    train_df = pd.read_csv(os.path.join(ROOT, "data", "train.csv"))
    val_df = pd.read_csv(os.path.join(ROOT, "data", "val.csv"))

    train_df["label"] = train_df["label"].apply(remap_label)
    val_df["label"] = val_df["label"].apply(remap_label)

    print(f"Train: {len(train_df)}, Val: {len(val_df)}")
    print("Train label distribution:")
    print(train_df["label"].value_counts().sort_index())

    tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=NUM_LABELS
    )

    train_dataset = EmailDataset(train_df["text"], train_df["label"], tokenizer)
    val_dataset = EmailDataset(val_df["text"], val_df["label"], tokenizer)

    training_args = TrainingArguments(
        output_dir=os.path.join(ROOT, "models", "training_output"),
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=100,
        learning_rate=2e-5,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    print("Training...")
    trainer.train()

    print(f"Saving model to {MODEL_DIR}...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)

    metrics = trainer.evaluate()
    print(f"Evaluation: {metrics}")

if __name__ == "__main__":
    main()
