import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.services.classifier import EmailClassifier
from app.services.rag import EmailRAG
from app.services.local_responder import generate_response, generate_summary

CATEGORIES = [
    "deadline", "interview_call", "news",
    "confirmation_email", "otp", "expired_email", "other",
]

CATEGORY_ACTIONS = {
    "deadline": "REMIND", "interview_call": "KEEP", "news": "ARCHIVE",
    "confirmation_email": "ARCHIVE", "otp": "DELETE",
    "expired_email": "DELETE", "other": "KEEP",
}

class EmailAgentWithRAG:
    def __init__(self):
        print("Initializing EmailAgentWithRAG...")
        self.classifier = EmailClassifier()
        self.rag = EmailRAG()
        self.has_llm = self.rag.llm is not None
        print(f"Local mode: {'LLM available' if self.has_llm else 'using templates'}")

    def process_query(self, query: str) -> dict:
        query_lower = query.lower()
        search_results = self.rag.search(query, k=5)
        if not search_results:
            search_results = self.rag.search_by_keyword(query, k=5)

        recommendations = self._generate_recommendations(search_results)

        if self.has_llm:
            try:
                from app.core.prompts import SYSTEM_PROMPT, RAG_RESPONSE_PROMPT
                context = self._build_context(search_results)
                prompt = RAG_RESPONSE_PROMPT.format(context=context, query=query)
                response = self.rag.llm.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                )
                reply = response.choices[0].message.content
            except Exception as e:
                print(f"LLM failed, using local responder: {e}")
                reply = generate_response(query, search_results, recommendations)
        else:
            reply = generate_response(query, search_results, recommendations)

        return {
            "reply": reply,
            "retrieved_emails": len(search_results),
            "recommendations": recommendations,
        }

    def _get_email_body(self, result: dict) -> str:
        for key in ("email", "text", "body", "content"):
            if key in result:
                return str(result[key])
        return str(result)

    def _build_context(self, results: list) -> str:
        if not results:
            return "No emails found matching your search."
        parts = []
        for i, r in enumerate(results[:5], 1):
            body = self._get_email_body(r)[:500]
            score = r.get("score", 0.0)
            parts.append(f"Email {i} (relevance: {score:.3f}):\n{body}")
        return "\n\n---\n\n".join(parts)

    def _generate_recommendations(self, results: list) -> list:
        top = results[:3]
        if not top:
            return []
        bodies = [self._get_email_body(r) for r in top]
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
        action = CATEGORY_ACTIONS.get(category)
        if action is None:
            return "KEEP"
        return action
