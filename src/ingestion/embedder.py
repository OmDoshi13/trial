"""Embedding generation using Ollama's API.

Uses the Ollama REST API directly (no LangChain dependency)
to generate embeddings for text chunks.
"""

import httpx
from src.config import settings


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using Ollama.

    Calls Ollama's /api/embed endpoint for each text.
    """
    embeddings = []
    for text in texts:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/embed",
            json={
                "model": settings.embedding_model,
                "input": text,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        # Ollama returns {"embeddings": [[...]]}
        embeddings.append(data["embeddings"][0])
    return embeddings


def get_single_embedding(text: str) -> list[float]:
    """Generate embedding for a single text string."""
    return get_embeddings([text])[0]
