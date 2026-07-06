# app/services/rag.py
"""
RAG pipeline using FAISS for semantic search.
Handles ANY search query against your email data.
"""

import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class EmailRAG:
    def __init__(
        self,
        index_path:  str = "models/email_index.faiss",
        emails_path: str = "models/emails.json",
    ):
        print("Loading embedding model...")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # ── Load FAISS index ───────────────────────────────────────────────
        if not os.path.exists(index_path):
            print(f"⚠️  FAISS index not found at {index_path}")
            print("    Run: python app/services/build_rag_index.py")
            self.index  = None
            self.emails = []
        else:
            print("Loading FAISS index...")
            self.index = faiss.read_index(index_path)

            with open(emails_path, "r", encoding="utf-8") as f:
                self.emails = json.load(f)

            # FIX 1: detect index type and warn if L2 is used without
            # normalisation. Inner-product (IndexFlatIP) on unit-normalised
            # vectors == cosine similarity. L2 (IndexFlatL2) gives correct
            # ranking ONLY when vectors are also L2-normalised; if they are
            # not, scores are raw squared-distances (lower = better) but we
            # return them as-is and sort descending — which is backwards.
            # We normalise query embeddings below for both cases so at least
            # the query side is consistent with however the index was built.
            index_type = type(self.index).__name__
            if "IP" in index_type:
                self._higher_is_better = True   # cosine / inner product
            else:
                self._higher_is_better = False  # L2: lower distance = better
                print(
                    f"[INFO] FAISS index type is {index_type} (L2). "
                    "Scores will be distances - lower means more similar."
                )

            print(f"✅ Loaded {len(self.emails)} emails into RAG")

        # ── Groq LLM client ───────────────────────────────────────────────
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            print("⚠️  GROQ_API_KEY not found in .env — LLM calls will fail")
        self.llm = Groq(api_key=groq_key)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _get_email_text(self, email_entry) -> str:
        """
        FIX 2: emails.json may store each entry as a plain string OR as a
        dict with a 'text'/'body'/'email' key (depending on build_rag_index).
        Handle both so we never return a raw dict as context.
        """
        if isinstance(email_entry, str):
            return email_entry
        if isinstance(email_entry, dict):
            for key in ("text", "body", "email", "content"):
                if key in email_entry:
                    return str(email_entry[key])
            # fallback: join all string values
            return " ".join(str(v) for v in email_entry.values())
        return str(email_entry)

    def _embed(self, texts: list) -> np.ndarray:
        """
        Embed a list of strings and L2-normalise the result.
        Normalisation makes inner-product == cosine similarity, and keeps
        L2 distances consistent with cosine ordering when the index vectors
        were also normalised at build time.
        """
        vecs = self.embedder.encode(texts, convert_to_numpy=True)
        # L2-normalise each row in-place
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)   # avoid div-by-zero
        return (vecs / norms).astype("float32")

    # ── Public search API ─────────────────────────────────────────────────

    def search(self, query: str, k: int = 5) -> list:
        """
        Semantic search over the FAISS index.

        Returns a list of dicts:
            { 'email': <str>, 'score': <float> }
        where 'email' is always a plain string (never a raw dict).

        FIX 3: query embedding is now L2-normalised before FAISS search
        (was missing before — caused cosine similarity to degrade to
        unnormalised dot product, hurting ranking quality silently).
        """
        if self.index is None or not self.emails:
            return []

        query_vec = self._embed([query])                        # shape (1, D)
        distances, indices = self.index.search(query_vec, k)   # both shape (1, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(self.emails):           # FAISS returns -1 for padding
                continue
            results.append({
                "email": self._get_email_text(self.emails[idx]),
                "score": float(dist),
            })

        # FIX 4: sort correctly based on index type.
        # L2 → lower score = more similar → sort ascending
        # IP  → higher score = more similar → sort descending (FAISS already
        #        returns results in this order, but explicit sort is safer)
        results.sort(key=lambda r: r["score"], reverse=self._higher_is_better)

        return results

    def search_by_keyword(self, query: str, k: int = 5) -> list:
        """
        Exact-match keyword fallback when semantic search returns nothing.

        FIX 5: now calls _get_email_text() so keyword matching runs against
        the plain text string, not repr(dict).
        """
        query_lower = query.lower()
        scored = []
        for entry in self.emails:
            text = self._get_email_text(entry)
            if query_lower in text.lower():
                scored.append({"email": text, "score": 1.0})

        # Secondary rank: prefer entries where query appears more times
        scored.sort(
            key=lambda r: r["email"].lower().count(query_lower),
            reverse=True,
        )
        return scored[:k]

    def process_query(self, query: str, k: int = 5) -> dict:
        """
        Complete RAG pipeline with keyword fallback.
        Returns { 'results': [...], 'context': <str> }
        """
        results = self.search(query, k)

        if not results:
            print(f"ℹ️  Semantic search returned nothing for '{query}', trying keyword fallback")
            results = self.search_by_keyword(query, k)

        context = "\n---\n".join(r["email"][:300] for r in results)
        return {"results": results, "context": context}


# ── Smoke test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rag = EmailRAG()

    if rag.index is not None:
        test_queries = [
            "Amazon order",
            "interview invitation",
            "deadline reminder",
            "verification code",
            "work emails",
        ]

        for query in test_queries:
            print(f"\nSearching: '{query}'")
            results = rag.search(query, k=3)
            if results:
                for r in results:
                    print(f"  Score : {r['score']:.4f}")
                    print(f"  Email : {r['email'][:100]}...")
                    print("-" * 40)
            else:
                print("  No results found")