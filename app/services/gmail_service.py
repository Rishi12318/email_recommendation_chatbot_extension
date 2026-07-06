import os
import json
import base64
from email import message_from_bytes
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.services.gmail_auth import refresh_token_if_expired

TOKEN_FILE = "gmail_token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def save_token(creds):
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)

def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def get_service():
    creds_dict = load_token()
    if not creds_dict:
        return None
    creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)
    if creds.expired and creds.refresh_token:
        creds = refresh_token_if_expired(creds_dict)
        save_token(creds)
    return build("gmail", "v1", credentials=creds)

def fetch_recent_emails(max_results=20):
    service = get_service()
    if not service:
        return {"error": "Not authenticated. Connect Gmail first."}
    try:
        results = service.users().messages().list(userId="me", maxResults=max_results, q="in:inbox").execute()
        messages = results.get("messages", [])
        emails = []
        for msg in messages:
            data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            payload = data.get("payload", {})
            headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
            body = _extract_body(payload)
            emails.append({
                "id": msg["id"],
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", "Unknown"),
                "date": headers.get("Date", ""),
                "snippet": data.get("snippet", ""),
                "body": body[:2000],
            })
        return {"emails": emails, "total": len(emails)}
    except Exception as e:
        return {"error": str(e)}

def _extract_body(payload):
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain" and "data" in part["body"]:
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
            if "parts" in part:
                return _extract_body(part)
    if "data" in payload.get("body", {}):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    return ""
