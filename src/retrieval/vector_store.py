"""ChromaDB vector store — stores document chunks and runs similarity search."""

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
import httpx

from src.config import settings


class OllamaEmbeddingFunction(EmbeddingFunction):
    """Generates embeddings by calling the local Ollama API."""

    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url

    def __call__(self, input: Documents) -> Embeddings:
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
    """Thin wrapper around a ChromaDB collection for add/query/clear."""

    def __init__(self):
        self.embedding_fn = OllamaEmbeddingFunction(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )
        self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self.collection = self.client.get_or_create_collection(
            name="trenkwalder_docs",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, texts: list[str], metadatas: list[dict], ids: list[str]):
        """Upsert document chunks into the collection."""
        self.collection.upsert(documents=texts, metadatas=metadatas, ids=ids)

    def query(self, query_text: str, n_results: int = 3, where: dict | None = None) -> list[dict]:
        """Return the top-N most similar chunks for a query."""
        kwargs: dict = {"query_texts": [query_text], "n_results": n_results}
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        chunks = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                chunks.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        return chunks

    @property
    def count(self) -> int:
        return self.collection.count()

    def clear_uploads(self) -> int:
        """Delete only chunks tagged as uploaded."""
        try:
            results = self.collection.get(where={"uploaded": "true"})
            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])
                return len(results["ids"])
        except Exception:
            pass
        return 0

    def clear_all(self) -> int:
        """Drop and recreate the collection (full wipe)."""
        count = self.count
        self.client.delete_collection("trenkwalder_docs")
        self.collection = self.client.get_or_create_collection(
            name="trenkwalder_docs",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        return count


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Lazy singleton so every module shares one store instance."""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
