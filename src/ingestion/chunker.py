"""Text chunking for document ingestion.

Splits documents into overlapping chunks for better retrieval quality.
Uses a recursive character-based splitting approach.
"""

from dataclasses import dataclass


@dataclass
class Chunk:
    """A chunk of text with metadata for vector storage."""
    text: str
    source: str
    format: str
    title: str
    chunk_index: int


def split_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    """Split text into overlapping chunks.

    Uses a hierarchy of separators (double newline → single newline →
    sentence boundary → hard character split) so that even PDFs whose
    text has only single-newline breaks are chunked properly.
    """
    separators = ["\n\n", "\n", ". ", " "]

    def _split_recursive(text: str, sep_idx: int = 0) -> list[str]:
        """Recursively split *text* into pieces ≤ chunk_size."""
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        # Try each separator from coarsest to finest
        while sep_idx < len(separators):
            sep = separators[sep_idx]
            parts = text.split(sep)
            if len(parts) > 1:
                # Merge parts back into chunks that fit within chunk_size
                chunks: list[str] = []
                current = ""
                for part in parts:
                    candidate = (current + sep + part) if current else part
                    if len(candidate) <= chunk_size:
                        current = candidate
                    else:
                        if current:
                            chunks.append(current.strip())
                        # If the single part itself exceeds chunk_size, recurse
                        if len(part) > chunk_size:
                            chunks.extend(_split_recursive(part, sep_idx + 1))
                            current = ""
                        else:
                            current = part
                if current.strip():
                    chunks.append(current.strip())
                return chunks
            sep_idx += 1

        # Fallback: hard character-level split
        chunks = []
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunks.append(text[i : i + chunk_size].strip())
        return [c for c in chunks if c]

    raw_chunks = _split_recursive(text)

    # Add overlap between consecutive chunks for context continuity
    final_chunks: list[str] = []
    for i, chunk in enumerate(raw_chunks):
        if i > 0 and chunk_overlap > 0:
            prev_tail = raw_chunks[i - 1][-chunk_overlap:]
            chunk = prev_tail + " " + chunk
        final_chunks.append(chunk.strip())

    return final_chunks


def chunk_document(doc, chunk_size: int = 500, chunk_overlap: int = 50) -> list[Chunk]:
    """Split a Document into Chunks with metadata preserved."""
    text_chunks = split_text(doc.content, chunk_size, chunk_overlap)
    return [
        Chunk(
            text=text,
            source=doc.source,
            format=doc.format,
            title=doc.title,
            chunk_index=i,
        )
        for i, text in enumerate(text_chunks)
    ]
