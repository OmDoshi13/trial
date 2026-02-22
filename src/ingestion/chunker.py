"""Splits documents into overlapping chunks for vector storage."""

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str
    format: str
    title: str
    chunk_index: int


def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Split text into overlapping pieces using progressively finer separators."""
    separators = ["\n\n", "\n", ". ", " "]

    def _split_recursive(text: str, sep_idx: int = 0) -> list[str]:
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        while sep_idx < len(separators):
            sep = separators[sep_idx]
            parts = text.split(sep)
            if len(parts) > 1:
                chunks: list[str] = []
                current = ""
                for part in parts:
                    candidate = (current + sep + part) if current else part
                    if len(candidate) <= chunk_size:
                        current = candidate
                    else:
                        if current:
                            chunks.append(current.strip())
                        if len(part) > chunk_size:
                            chunks.extend(_split_recursive(part, sep_idx + 1))
                            current = ""
                        else:
                            current = part
                if current.strip():
                    chunks.append(current.strip())
                return chunks
            sep_idx += 1

        # Fallback: hard split by character count
        chunks = []
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunks.append(text[i : i + chunk_size].strip())
        return [c for c in chunks if c]

    raw_chunks = _split_recursive(text)

    # Prepend tail of previous chunk for overlap / context continuity
    final_chunks: list[str] = []
    for i, chunk in enumerate(raw_chunks):
        if i > 0 and chunk_overlap > 0:
            prev_tail = raw_chunks[i - 1][-chunk_overlap:]
            chunk = prev_tail + " " + chunk
        final_chunks.append(chunk.strip())

    return final_chunks


def chunk_document(doc, chunk_size: int = 500, chunk_overlap: int = 50) -> list[Chunk]:
    """Turn a Document into a list of Chunks with metadata."""
    text_chunks = split_text(doc.content, chunk_size, chunk_overlap)
    return [
        Chunk(text=text, source=doc.source, format=doc.format,
              title=doc.title, chunk_index=i)
        for i, text in enumerate(text_chunks)
    ]
