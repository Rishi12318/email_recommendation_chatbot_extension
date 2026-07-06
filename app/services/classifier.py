# app/services/classifier.py
import os
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

class EmailClassifier:
    def __init__(self, model_path="models/email_classifier"):
        self.categories = ['deadline', 'interview_call', 'news', 
                          'confirmation_email', 'otp', 'expired_email', 'other']
        
        if not os.path.exists(model_path):
            print(f"⚠️ Model not found at {model_path}")
            print("Using dummy classifier")
            self.tokenizer = None
            self.model = None
            self.device = "cpu"
            return
        
        try:
            self.tokenizer = DistilBertTokenizer.from_pretrained(model_path)
            self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            print(f"✅ Classifier loaded from {model_path}")
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            self.tokenizer = None
            self.model = None
            self.device = "cpu"

    def predict(self, text):
        if self.model is None or self.tokenizer is None:
            return "other"
        
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            self.model.eval()
            with torch.no_grad():
                outputs = self.model(**inputs)
                prediction = torch.argmax(outputs.logits, dim=-1)

            return self.categories[prediction.item()]
        except Exception as e:
            print(f"Prediction error: {e}")
            return "other"

    def predict_batch(self, texts):
        """Batch prediction for multiple emails."""
        if self.model is None or self.tokenizer is None:
            return ["other"] * len(texts)
        
        try:
            inputs = self.tokenizer(
                texts,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            self.model.eval()
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.argmax(outputs.logits, dim=-1)

            return [self.categories[p.item()] for p in predictions]
        except Exception as e:
            print(f"Batch prediction error: {e}")
            return ["other"] * len(texts)