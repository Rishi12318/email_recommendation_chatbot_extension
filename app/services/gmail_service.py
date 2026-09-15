import os
import json
import re
import base64
from datetime import datetime
from email.utils import parsedate_to_datetime
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


def _parse_sender(raw_from):
    if not raw_from or raw_from == "Unknown":
        return {"name": "Unknown", "email": ""}
    match = re.match(r'^"?(.+?)"?\s*<(.+?)>', raw_from)
    if match:
        return {"name": match.group(1).strip(), "email": match.group(2).strip()}
    if "@" in raw_from:
        return {"name": raw_from.split("@")[0].strip(), "email": raw_from.strip()}
    return {"name": raw_from.strip(), "email": ""}


def _parse_date(raw_date):
    if not raw_date:
        return {"raw": "", "iso": "", "display": ""}
    try:
        dt = parsedate_to_datetime(raw_date)
        return {
            "raw": raw_date,
            "iso": dt.isoformat(),
            "display": dt.strftime("%Y-%m-%d %H:%M"),
        }
    except Exception:
        return {"raw": raw_date, "iso": "", "display": raw_date}


def fetch_recent_emails(max_results=20):
    service = get_service()
    if not service:
        return {"error": "Not authenticated. Connect Gmail first."}
    try:
        emails = []
        page_token = None
        fetched = 0
        while fetched < max_results:
            batch_size = min(50, max_results - fetched)
            params = {"userId": "me", "maxResults": batch_size, "q": "in:inbox"}
            if page_token:
                params["pageToken"] = page_token
            results = service.users().messages().list(**params).execute()
            messages = results.get("messages", [])
            if not messages:
                break
            for msg in messages:
                try:
                    data = service.users().messages().get(
                        userId="me", id=msg["id"], format="full"
                    ).execute()
                    payload = data.get("payload", {})
                    headers = {
                        h["name"]: h["value"]
                        for h in payload.get("headers", [])
                    }
                    body = _extract_body(payload)
                    sender = _parse_sender(headers.get("From", "Unknown"))
                    date_info = _parse_date(headers.get("Date", ""))
                    emails.append({
                        "id": msg["id"],
                        "subject": headers.get("Subject", "(no subject)"),
                        "sender_name": sender["name"],
                        "sender_email": sender["email"],
                        "from": headers.get("From", "Unknown"),
                        "date": date_info["raw"],
                        "date_iso": date_info["iso"],
                        "date_display": date_info["display"],
                        "snippet": data.get("snippet", ""),
                        "body": body[:2000],
                    })
                except Exception:
                    continue
            fetched += len(messages)
            page_token = results.get("nextPageToken")
            if not page_token:
                break
        return {"emails": emails, "total": len(emails)}
    except Exception as e:
        return {"error": str(e)}


def _extract_body(payload):
    try:
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    body_data = part.get("body", {}).get("data")
                    if body_data:
                        return base64.urlsafe_b64decode(body_data).decode(
                            "utf-8", errors="ignore"
                        )
                if "parts" in part:
                    result = _extract_body(part)
                    if result:
                        return result
        body_data = payload.get("body", {}).get("data")
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode(
                "utf-8", errors="ignore"
            )
    except Exception:
        pass
    return ""
