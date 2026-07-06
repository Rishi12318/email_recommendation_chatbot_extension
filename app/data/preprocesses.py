# app/data/preprocess.py
import pandas as pd
import re

def clean_email_for_rag(text):
    """Clean email for RAG - remove forward indicators only"""
    if not isinstance(text, str):
        return ""

    # Remove forward indicators
    text = re.sub(r'^FW: |^Fwd: |^FW : |^Forwarded message: ', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\[Fwd:.*\]', '', text, flags=re.MULTILINE)
    text = re.sub(r'-------- Forwarded Message --------.*$', '', text, flags=re.DOTALL | re.MULTILINE)
    text = re.sub(r'Begin forwarded message:.*$', '', text, flags=re.DOTALL | re.MULTILINE)
    text = re.sub(r'---------- Forwarded message ----------.*$', '', text, flags=re.DOTALL | re.MULTILINE)

    # Remove CC
    text = re.sub(r'^Cc:.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^CC:.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^cc:.*$', '', text, flags=re.MULTILINE)

    # Remove footers
    text = re.sub(r'Get Outlook for (iOS|Android|macOS|Windows).*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'Sent from my (iPhone|iPad|Android|BlackBerry|Samsung).*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'This email is confidential.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'CONFIDENTIALITY NOTICE.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'Please consider the environment before printing.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'Disclaimer:.*$', '', text, flags=re.DOTALL)
    text = re.sub(r'This message and any attachments.*$', '', text, flags=re.DOTALL)

    # Remove HTML
    text = re.sub(r'<.*?>', '', text)

    # Remove emojis
    emoji_pattern = re.compile("[" + u"\U0001F600-\U0001F64F" + u"\U0001F300-\U0001F5FF" + u"\U0001F680-\U0001F6FF" + u"\U0001F1E0-\U0001F1FF" + u"\U00002500-\U00002BEF" + u"\U00002702-\U000027B0" + u"\U000024C2-\U0001F251" + u"\U0001f926-\U0001f937" + u"\U00010000-\U0010ffff" + u"\u2640-\u2642" + u"\u2600-\u2B55" + u"\u200d" + u"\u23cf" + u"\u23e9" + u"\u231a" + u"\ufe0f" + u"\u3030" + "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)

    # Keep meaningful content
    text = re.sub(r'[^a-zA-Z0-9\s\.!?;:@#>]', ' ', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def preprocess_for_rag(df, text_column='text'):
    """Preprocess for RAG"""
    df = df.copy()
    df['cleaned_text'] = df[text_column].apply(clean_email_for_rag)
    df = df[df['cleaned_text'].str.len() > 20]
    return df