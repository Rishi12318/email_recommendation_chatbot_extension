# app/services/agent_rag.py
"""
Complete agent with RAG + Classifier + LLM integration.
Handles ANY user query about emails using semantic search + trained model + Groq.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.services.classifier import EmailClassifier
from app.services.rag import EmailRAG
from app.core.prompts import SYSTEM_PROMPT, RAG_RESPONSE_PROMPT


# Must match CATEGORIES in train.py exactly
CATEGORIES = [
    "deadline",
    "interview_call",
    "news",
    "confirmation_email",
    "otp",
    "expired_email",
    "other",
]

# Rule-based actions
CATEGORY_ACTIONS = {
    "deadline":           "REMIND",
    "interview_call":     "KEEP",
    "news":               "ARCHIVE",
    "confirmation_email": "ARCHIVE",
    "otp":                "DELETE",
    "expired_email":      "DELETE",
    "other":              "KEEP",
}


class EmailAgentWithRAG:
    def __init__(self):
        print("Initializing EmailAgentWithRAG...")
        self.classifier = EmailClassifier()
        self.rag = EmailRAG()
        print("✅ EmailAgentWithRAG ready")

    def process_query(self, query: str) -> dict:
        """
        Full pipeline: RAG search → classify retrieved emails → generate response.
        Uses trained DistilBERT model + FAISS RAG + Groq LLM.
        """
        # Step 1: Semantic search over email store (RAG)
        search_results = self.rag.search(query, k=5)

        # Step 2: Build LLM context from top results
        context = self._build_context(search_results)

        # Step 3: Generate response using Groq LLM
        prompt = RAG_RESPONSE_PROMPT.format(context=context, query=query)

        response = self.rag.llm.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        # Step 4: Classify retrieved emails and build recommendations
        recommendations = self._generate_recommendations(search_results)

        return {
            "reply": response.choices[0].message.content,
            "retrieved_emails": len(search_results),
            "recommendations": recommendations,
        }

    def _get_email_body(self, result: dict) -> str:
        """Safely extract email text from search result dict."""
        for key in ("email", "text", "body", "content"):
            if key in result:
                return str(result[key])
        return str(result)

    def _build_context(self, results: list) -> str:
        """Build LLM-ready context string from RAG search results."""
        if not results:
            return "No emails found matching your search."

        parts = []
        for i, r in enumerate(results[:5], 1):
            body = self._get_email_body(r)[:500]
            score = r.get("score", 0.0)
            parts.append(f"Email {i} (relevance: {score:.3f}):\n{body}")

        return "\n\n---\n\n".join(parts)

    def _generate_recommendations(self, results: list) -> list:
        """Classify top-3 retrieved emails and return action recommendations."""
        top = results[:3]
        if not top:
            return []

        bodies = [self._get_email_body(r) for r in top]

        # Use trained classifier
        categories = []
        for body in bodies:
            try:
                cat = self.classifier.predict(body[:1000])
                categories.append(cat)
            except Exception as e:
                print(f"Classification error: {e}")
                categories.append("other")

        recommendations = []
        for r, body, category in zip(top, bodies, categories):
            recommendations.append({
                "email": body[:100] + "...",
                "category": category,
                "action": self._recommend_action(category),
            })

        return recommendations

    def _recommend_action(self, category: str) -> str:
        """Rule-based action for a classified email category."""
        action = CATEGORY_ACTIONS.get(category)
        if action is None:
            print(f"[WARN] Unknown category '{category}', defaulting to KEEP")
            return "KEEP"
        return action


# ── Smoke test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    agent = EmailAgentWithRAG()

    test_queries = [
        "Show me emails from Amazon",
        "Delete expired emails",
        "Remind me about upcoming deadlines",
        "Summarize my recent emails",
        "Show me confirmation emails",
    ]

    for query in test_queries:
        print("\n" + "=" * 60)
        print(f"Query: {query}")
        print("-" * 60)
        try:
            result = agent.process_query(query)
            print(f"Retrieved : {result['retrieved_emails']} emails")
            print(f"Reply     : {result['reply'][:300]}...")
            print(f"Actions   :")
            for rec in result["recommendations"]:
                print(f"  [{rec['action']:7}] ({rec['category']}) {rec['email'][:80]}")
        except Exception as e:
            print(f"Error: {e}")