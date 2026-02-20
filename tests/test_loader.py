"""Tests for document loader."""

import tempfile
from pathlib import Path
from src.ingestion.loader import load_txt, load_markdown, load_documents


def test_load_txt():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello, this is a test document.")
        f.flush()
        doc = load_txt(Path(f.name))
        assert doc.content == "Hello, this is a test document."
        assert doc.format == "txt"


def test_load_markdown():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Title\n\nSome **bold** text.")
        f.flush()
        doc = load_markdown(Path(f.name))
        assert "Title" in doc.content
        assert "bold" in doc.content
        assert doc.format == "md"


def test_load_documents_from_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        p = Path(tmpdir) / "test.txt"
        p.write_text("Test content")

        docs = load_documents(Path(tmpdir))
        assert len(docs) == 1
        assert docs[0].content == "Test content"
