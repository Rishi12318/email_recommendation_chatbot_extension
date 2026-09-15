import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import numpy as np


@pytest.fixture
def client():
    from app import main as main_mod

    mock_agent = MagicMock()
    mock_agent.process_query.return_value = {
        "reply": "Found 2 emails from Amazon.",
        "recommendations": [{"email": "test", "category": "news", "action": "ARCHIVE"}],
        "retrieved_emails": 2,
    }

    mock_rag = MagicMock()
    mock_rag.emails = []
    mock_rag.index = MagicMock()
    mock_rag.index.ntotal = 0
    mock_rag.index.add = MagicMock()

    main_mod.agent = mock_agent
    main_mod.rag = mock_rag
    main_mod.get_agent = lambda: mock_agent
    main_mod.get_rag = lambda: mock_rag

    with TestClient(main_mod.app) as c:
        yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_success(client):
    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "Show me emails from Amazon"}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "recommendations" in data
    assert data["end_of_conversation"] is False


def test_chat_empty_messages(client):
    response = client.post("/api/chat", json={"messages": []})
    assert response.status_code == 400


def test_gmail_status(client):
    response = client.get("/api/gmail/status")
    assert response.status_code == 200
    data = response.json()
    assert "connected" in data
    assert isinstance(data["connected"], bool)


def test_list_emails(client):
    response = client.get("/api/gmail/emails")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "recent" in data
    assert isinstance(data["recent"], list)


def test_ingest_emails_empty(client):
    response = client.post("/api/emails/ingest", json={"emails": []})
    assert response.status_code == 400


def test_ingest_emails(client):
    from app import main as main_mod

    mock_embedder_instance = MagicMock()
    fake_vecs = np.random.rand(1, 384).astype("float32")
    mock_embedder_instance.encode.return_value = fake_vecs

    mock_sentence_transformers = MagicMock()
    mock_sentence_transformers.SentenceTransformer.return_value = mock_embedder_instance

    mock_faiss = MagicMock()

    with patch.dict("sys.modules", {
        "sentence_transformers": mock_sentence_transformers,
        "faiss": mock_faiss,
    }):
        response = client.post(
            "/api/emails/ingest",
            json={
                "emails": [
                    {
                        "sender": "test@example.com",
                        "subject": "Test Subject",
                        "snippet": "Test body",
                        "date": "2026-01-01",
                    }
                ]
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "indexed" in data
    assert "total" in data
