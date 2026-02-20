"""Tests for text chunker."""

from src.ingestion.chunker import split_text


def test_split_short_text():
    text = "Short text."
    chunks = split_text(text, chunk_size=500, chunk_overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == "Short text."


def test_split_long_text():
    paragraphs = ["Paragraph " + str(i) + ". " + "x" * 100 for i in range(20)]
    text = "\n\n".join(paragraphs)
    chunks = split_text(text, chunk_size=300, chunk_overlap=30)
    assert len(chunks) > 1
    # All chunks should have content
    for chunk in chunks:
        assert len(chunk) > 0


def test_overlap():
    text = "Para one with some content here.\n\nPara two with different content.\n\nPara three ends here."
    chunks = split_text(text, chunk_size=60, chunk_overlap=10)
    # With overlap, consecutive chunks should share some text
    assert len(chunks) >= 2
