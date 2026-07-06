# app/main.py
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import List
from pydantic import Field
import uvicorn
from app.services.agent_rag import EmailAgentWithRAG
from app.services.gmail_auth import get_auth_url, exchange_code
from app.services.gmail_service import fetch_recent_emails, save_token
from app.services.rag import EmailRAG

app = FastAPI()
agent = None
rag = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "chrome-extension://*",
        os.getenv("RENDER_EXTERNAL_URL", ""),
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ScrapedEmail(BaseModel):
    sender: str = ""
    subject: str = ""
    snippet: str = ""
    date: str = ""
    body: str = ""

class IngestRequest(BaseModel):
    emails: List[ScrapedEmail]

class ChatResponse(BaseModel):
    reply: str
    recommendations: List[dict] = []
    end_of_conversation: bool = False


def get_agent() -> EmailAgentWithRAG:
    global agent
    if agent is None:
        agent = EmailAgentWithRAG()
    return agent

def get_rag() -> EmailRAG:
    global rag
    if rag is None:
        rag = EmailRAG()
    return rag


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    user_message = request.messages[-1].content
    try:
        result = get_agent().process_query(user_message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat pipeline failed: {exc}")
    return ChatResponse(
        reply=result.get("reply", "No response generated"),
        recommendations=result.get("recommendations", []),
        end_of_conversation=False,
    )


@app.get("/api/gmail/auth")
async def gmail_auth():
    try:
        auth_url = get_auth_url()
        return RedirectResponse(auth_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth setup failed: {e}")


@app.get("/api/gmail/callback")
async def gmail_callback(code: str):
    try:
        creds = exchange_code(code)
        save_token(creds)
        return HTMLResponse("<h2>Gmail Connected! You can close this tab.</h2><script>window.close()</script>")
    except Exception as e:
        return HTMLResponse(f"<h2>Auth failed: {e}</h2>")


@app.get("/api/gmail/status")
async def gmail_status():
    token_file = "gmail_token.json"
    return {"connected": os.path.exists(token_file)}


@app.post("/api/gmail/scan")
async def gmail_scan():
    result = fetch_recent_emails(max_results=50)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/gmail/index")
async def gmail_index():
    result = fetch_recent_emails(max_results=50)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    emails = result.get("emails", [])
    if not emails:
        return {"indexed": 0}
    rag = get_rag()
    new_count = 0
    for email in emails:
        text = f"From: {email['from']}\nSubject: {email['subject']}\nDate: {email['date']}\n\n{email['body']}"
        if text not in rag.emails:
            rag.emails.append(text)
            new_count += 1
    with open("models/emails.json", "w", encoding="utf-8") as f:
        json.dump(rag.emails, f, ensure_ascii=False, indent=2)
    import faiss, numpy as np
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    if new_count > 0:
        new_texts = [e for e in emails]
        new_vecs = embedder.encode([f"From: {e['from']}\nSubject: {e['subject']}\nDate: {e['date']}\n\n{e['body']}" for e in emails], convert_to_numpy=True)
        norms = np.linalg.norm(new_vecs, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        new_vecs = (new_vecs / norms).astype("float32")
        rag.index.add(new_vecs)
        faiss.write_index(rag.index, "models/email_index.faiss")
    return {"indexed": new_count, "total_emails": len(rag.emails)}


@app.get("/api/gmail/emails")
async def list_emails():
    rag = get_rag()
    return {"total": len(rag.emails), "recent": [e[:200] for e in rag.emails[-50:]]}


@app.post("/api/emails/ingest")
async def ingest_emails(request: IngestRequest):
    if not request.emails:
        raise HTTPException(status_code=400, detail="No emails provided")
    rag = get_rag()
    new_count = 0
    for email in request.emails:
        text = f"From: {email.sender}\nSubject: {email.subject}\nDate: {email.date or ''}\n\n{email.snippet or email.body or ''}"
        if text not in rag.emails:
            rag.emails.append(text)
            new_count += 1
    if new_count > 0:
        import faiss, numpy as np
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        new_texts = rag.emails[-new_count:]
        vecs = embedder.encode(new_texts, convert_to_numpy=True)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        vecs = (vecs / norms).astype("float32")
        rag.index.add(vecs)
        with open("models/emails.json", "w", encoding="utf-8") as f:
            json.dump(rag.emails, f, ensure_ascii=False, indent=2)
        faiss.write_index(rag.index, "models/email_index.faiss")
    return {"indexed": new_count, "total": len(rag.emails)}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)