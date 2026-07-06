# app/main.py (API Only)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
from app.services.agent_rag import EmailAgentWithRAG

app = FastAPI()
agent = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "chrome-extension://*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    reply: str
    recommendations: List[dict] = []
    end_of_conversation: bool = False


def get_agent() -> EmailAgentWithRAG:
    global agent
    if agent is None:
        agent = EmailAgentWithRAG()
    return agent

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)