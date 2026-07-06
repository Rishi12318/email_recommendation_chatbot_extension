# ============================================================
#  Email Classifier Training for Google Colab
# ============================================================
# Run this entire cell in Colab (Runtime -> Run all)
# No file uploads needed — it clones from GitHub.
# ============================================================

import os, sys, zipfile, subprocess

# --- Clone the repo ---
if not os.path.exists("email-recommendation"):
    !git clone https://github.com/Rishi12318/email_recommendation_chatbot_extension.git email-recommendation
    %cd email-recommendation
else:
    %cd email-recommendation

# --- Install dependencies ---
!pip install -q torch transformers pandas scikit-learn datasets accelerate sentence-transformers

# --- Imports ---
import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from sklearn.metrics import accuracy_score, f1_score, classification_report

CATEGORIES = [
    "deadline",
    "interview_call",
    "news",
    "confirmation_email",
    "otp",
    "expired_email",
    "other",
]

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
    train_df = pd.read_csv("data/train.csv")
    val_df = pd.read_csv("data/val.csv")

    train_df["label"] = train_df["label"].apply(remap_label)
    val_df["label"] = val_df["label"].apply(remap_label)

    print(f"Train: {len(train_df)}, Val: {len(val_df)}")
    print("\nTrain distribution:")
    print(train_df["label"].map(lambda i: CATEGORIES[i]).value_counts())

    print("\nLoading DistilBERT...")
    tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=len(CATEGORIES)
    )
    model = model.to("cuda")

    train_dataset = EmailDataset(train_df["text"], train_df["label"], tokenizer)
    val_dataset = EmailDataset(val_df["text"], val_df["label"], tokenizer)

    training_args = TrainingArguments(
        output_dir="./training_output",
        num_train_epochs=3,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=64,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_steps=50,
        learning_rate=2e-5,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        report_to="none",
        fp16=True,
        dataloader_num_workers=2,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    print("\nStarting training (3 epochs, ~13k samples)...")
    trainer.train()

    print("\nSaving model...")
    model_dir = "email_classifier_model"
    os.makedirs(model_dir, exist_ok=True)
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)

    print("\nEvaluating...")
    metrics = trainer.evaluate()
    print(f"Accuracy:  {metrics['eval_accuracy']:.4f}")
    print(f"F1 (weighted): {metrics['eval_f1_weighted']:.4f}")

    preds = trainer.predict(val_dataset)
    y_pred = preds.predictions.argmax(-1)
    y_true = preds.label_ids
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=CATEGORIES))

    print("\nZipping model for download...")
    zip_path = "email_classifier_model.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(model_dir):
            for file in files:
                zf.write(os.path.join(root, file),
                         os.path.relpath(os.path.join(root, file), "."))
    print(f"Model zipped to: {zip_path}")

    # Mount drive and copy there as backup
    try:
        from google.colab import drive
        drive.mount("/content/drive")
        !cp email_classifier_model.zip "/content/drive/MyDrive/"
        print("Also saved to Google Drive: email_classifier_model.zip")
    except:
        pass

    from google.colab import files
    files.download(zip_path)

if __name__ == "__main__":
    main()
