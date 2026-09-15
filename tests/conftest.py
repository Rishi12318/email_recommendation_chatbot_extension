"""
Pre-import mocks for heavy ML dependencies that cause import issues in test env.
Must run before any app module is imported.
"""
import sys
from unittest.mock import MagicMock

# Mock heavy deps so tests can import app modules without loading real models
_heavy_deps = [
    "faiss",
    "sentence_transformers",
    "sentence_transformers.SentenceTransformer",
    "torch",
    "transformers",
    "groq",
]

for dep in _heavy_deps:
    if dep not in sys.modules:
        sys.modules[dep] = MagicMock()
