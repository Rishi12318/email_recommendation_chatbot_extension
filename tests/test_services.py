import pytest
from unittest.mock import patch, MagicMock
from app.services.local_responder import (
    generate_response,
    generate_summary,
    generate_action_recommendation,
)
from app.services.agent_rag import CATEGORY_ACTIONS, CATEGORIES


class TestClassifier:
    def test_predict_without_model(self):
        from app.services.classifier import EmailClassifier

        clf = EmailClassifier.__new__(EmailClassifier)
        clf.categories = [
            "deadline", "interview_call", "news",
            "confirmation_email", "otp", "expired_email", "other",
        ]
        clf.tokenizer = None
        clf.model = None
        clf.device = "cpu"

        result = clf.predict("Test email text")
        assert result == "other"

    def test_predict_batch_without_model(self):
        from app.services.classifier import EmailClassifier

        clf = EmailClassifier.__new__(EmailClassifier)
        clf.categories = [
            "deadline", "interview_call", "news",
            "confirmation_email", "otp", "expired_email", "other",
        ]
        clf.tokenizer = None
        clf.model = None
        clf.device = "cpu"

        results = clf.predict_batch(["email 1", "email 2", "email 3"])
        assert results == ["other", "other", "other"]
        assert len(results) == 3

    def test_categories_list(self):
        from app.services.classifier import EmailClassifier

        clf = EmailClassifier.__new__(EmailClassifier)
        clf.categories = [
            "deadline", "interview_call", "news",
            "confirmation_email", "otp", "expired_email", "other",
        ]
        assert len(clf.categories) == 7
        assert "deadline" in clf.categories
        assert "otp" in clf.categories


class TestLocalResponder:
    def test_generate_response_no_results(self):
        result = generate_response("test query", [])
        assert result == "No emails found matching your query."

    def test_generate_response_with_results(self):
        results = [
            {"email": "From: test@example.com\nSubject: Hello\n\nBody text", "score": 0.9},
            {"email": "From: bob@example.com\nSubject: Hi\n\nAnother body", "score": 0.8},
        ]
        result = generate_response("test query", results)
        assert "2 emails" in result
        assert "test@example.com" in result

    def test_generate_response_with_classifications(self):
        results = [
            {"email": "From: test@example.com\nSubject: Hello\n\nBody text", "score": 0.9},
        ]
        classifications = [{"category": "news", "action": "ARCHIVE"}]
        result = generate_response("test query", results, classifications)
        assert "news" in result.lower() or "newsletter" in result.lower()

    def test_generate_summary_empty(self):
        result = generate_summary([])
        assert result == "No emails to summarize."

    def test_generate_summary_with_emails(self):
        emails = ["email1", "email2"]
        result = generate_summary(emails)
        assert "2 emails" in result

    def test_generate_action_recommendation(self):
        result = generate_action_recommendation("Test email body", "deadline")
        assert "deadline" in result.lower()
        assert "Test email body" in result


class TestAgentRAG:
    def test_category_actions(self):
        assert CATEGORY_ACTIONS["deadline"] == "REMIND"
        assert CATEGORY_ACTIONS["otp"] == "DELETE"
        assert CATEGORY_ACTIONS["news"] == "ARCHIVE"
        assert CATEGORY_ACTIONS["other"] == "KEEP"

    def test_categories_list(self):
        assert len(CATEGORIES) == 7
        assert "deadline" in CATEGORIES
        assert "interview_call" in CATEGORIES
