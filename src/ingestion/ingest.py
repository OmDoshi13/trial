"""Document ingestion pipeline.

Orchestrates: load documents → chunk → embed → store in ChromaDB.
Run this module directly to ingest all documents:
    python -m src.ingestion.ingest
"""

import sys
from pathlib import Path

# Ensure project root is on path when run as module
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import settings
from src.ingestion.loader import load_documents, load_single_file
from src.ingestion.chunker import chunk_document
from src.retrieval.vector_store import get_vector_store


def ingest_single_file(file_path: Path) -> dict:
    """Ingest a single uploaded file into the vector store.

    Returns a summary dict with ingestion stats.
    """
    # 1. Load the document
    doc = load_single_file(file_path)

    # 2. Chunk it
    chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)
    if not chunks:
        raise ValueError(f"No chunks produced from {file_path.name}")

    # 3. Store in vector DB
    store = get_vector_store()
    texts = [c.text for c in chunks]
    metadatas = [
        {
            "source": c.source,
            "format": c.format,
            "title": c.title,
            "chunk_index": c.chunk_index,
            "uploaded": "true",  # tag so we can distinguish uploads
        }
        for c in chunks
    ]
    ids = [f"upload_{c.title}_{c.chunk_index}" for c in chunks]

    store.add(texts=texts, metadatas=metadatas, ids=ids)

    return {
        "filename": file_path.name,
        "format": doc.format,
        "chunks": len(chunks),
        "total_docs_in_store": store.count,
    }


def ingest_all():
    """Main ingestion pipeline."""
    print("=" * 60)
    print("  Trenkwalder Chatbot — Document Ingestion")
    print("=" * 60)

    # 1. Load documents
    print(f"\n📂 Loading documents from: {settings.docs_path}")
    documents = load_documents(settings.docs_path)
    print(f"   ✓ Loaded {len(documents)} documents\n")

    if not documents:
        print("   ⚠ No documents found. Add files to the documents/ directory.")
        return

    # 2. Chunk documents
    print("✂  Chunking documents...")
    all_chunks = []
    for doc in documents:
        chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)
        all_chunks.extend(chunks)
        print(f"   {doc.title}.{doc.format} → {len(chunks)} chunks")
    print(f"   ✓ Total chunks: {len(all_chunks)}\n")

    # 3. Store in vector database (embedding happens inside ChromaDB via Ollama)
    print("💾 Storing in ChromaDB with embeddings...")
    store = get_vector_store()

    # Prepare data for ChromaDB
    texts = [c.text for c in all_chunks]
    metadatas = [
        {"source": c.source, "format": c.format, "title": c.title, "chunk_index": c.chunk_index}
        for c in all_chunks
    ]
    ids = [f"{c.title}_{c.chunk_index}" for c in all_chunks]

    store.add(texts=texts, metadatas=metadatas, ids=ids)
    print(f"   ✓ Stored {len(all_chunks)} chunks in vector store\n")

    print("=" * 60)
    print("  ✅ Ingestion complete!")
    print("=" * 60)


if __name__ == "__main__":
    ingest_all()
