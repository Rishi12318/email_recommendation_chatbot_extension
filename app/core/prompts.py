SYSTEM_PROMPT = """You are an AI email assistant. Help the user manage their inbox efficiently.
Be concise and direct. Provide actionable recommendations when possible."""

RAG_RESPONSE_PROMPT = """Based on the following emails from the user's inbox, answer their question.

Emails:
{context}

User question: {query}

Provide a clear, concise answer referencing specific emails when relevant."""
