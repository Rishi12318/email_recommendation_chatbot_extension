"""Downloads base DistilBERT model so the classifier loads without errors.
Replace the files with your Colab-trained model for accurate predictions."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

MODEL_DIR = os.path.join(ROOT, "models", "email_classifier")

from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

print("Downloading base DistilBERT model (this is a one-time download)...")
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased", num_labels=7
)

os.makedirs(MODEL_DIR, exist_ok=True)
model.save_pretrained(MODEL_DIR)
tokenizer.save_pretrained(MODEL_DIR)

print(f"Model saved to {MODEL_DIR}")
print()
print("To use your Colab-trained model:")
print("  1. In Colab, zip the model folder:")
print('     !zip -r /content/email_classifier.zip /content/models/email_classifier/')
print("  2. Download the zip:")
print('     from google.colab import files')
print('     files.download("/content/email_classifier.zip")')
print(f"  3. Extract the zip into {MODEL_DIR}")
