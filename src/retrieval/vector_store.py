"""ChromaDB vector store wrapper.

Uses Ollama embeddings via a custom embedding function for ChromaDB.
Provides a clean interface for adding and querying document chunks.
"""

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
import httpx

from src.config import settings


class OllamaEmbeddingFunction(EmbeddingFunction):
    """Custom ChromaDB embedding function that uses Ollama."""

    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for a list of documents."""
        embeddings = []
        for text in input:
            response = httpx.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model, "input": text},
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["embeddings"][0])
        return embeddings


class VectorStore:
    """Wrapper around ChromaDB for document storage and retrieval."""

    def __init__(self):
        self.embedding_fn = OllamaEmbeddingFunction(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_path),
        )
        self.collection = self.client.get_or_create_collection(
            name="trenkwalder_docs",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, texts: list[str], metadatas: list[dict], ids: list[str]):
        """Add documents to the vector store."""
        # ChromaDB handles embedding via our custom function
        self.collection.upsert(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

    def query(self, query_text: str, n_results: int = 3, where: dict | None = None) -> list[dict]:
        """Query the vector store and return relevant chunks with metadata.

        Args:
            query_text: The text to search for.
            n_results: Maximum number of results.
            where: Optional ChromaDB metadata filter, e.g. {"uploaded": "true"}.
        """
        kwargs: dict = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        # Format results into a clean list
        chunks = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                chunk = {
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                }
                chunks.append(chunk)
        return chunks

    @property
    def count(self) -> int:
        """Return the number of documents in the store."""
        return self.collection.count()


# Module-level singleton
_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get or create the vector store singleton."""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
