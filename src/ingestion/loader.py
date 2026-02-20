"""Multi-format document loader.

Supports PDF, TXT, and Markdown files using a strategy pattern —
each format has its own loader function, making it easy to extend.
"""

from pathlib import Path
from dataclasses import dataclass
import fitz  # PyMuPDF
import markdown
from bs4 import BeautifulSoup


@dataclass
class Document:
    """Represents a loaded document with its content and metadata."""
    content: str
    source: str          # file path
    format: str          # pdf, txt, md
    title: str           # filename without extension


def load_pdf(path: Path) -> Document:
    """Extract text from a PDF file using PyMuPDF."""
    doc = fitz.open(str(path))
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return Document(
        content="\n".join(text_parts).strip(),
        source=str(path),
        format="pdf",
        title=path.stem,
    )


def load_txt(path: Path) -> Document:
    """Load plain text file."""
    content = path.read_text(encoding="utf-8")
    return Document(
        content=content.strip(),
        source=str(path),
        format="txt",
        title=path.stem,
    )


def load_markdown(path: Path) -> Document:
    """Load Markdown file and convert to plain text."""
    raw = path.read_text(encoding="utf-8")
    html = markdown.markdown(raw, extensions=["tables", "fenced_code"])
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    return Document(
        content=text.strip(),
        source=str(path),
        format="md",
        title=path.stem,
    )


# Strategy mapping: file extension → loader function
LOADERS = {
    ".pdf": load_pdf,
    ".txt": load_txt,
    ".md": load_markdown,
}

# Supported extensions for upload validation
SUPPORTED_EXTENSIONS = set(LOADERS.keys())


def load_single_file(path: Path) -> Document:
    """Load a single file by path. Raises ValueError if format unsupported."""
    ext = path.suffix.lower()
    loader = LOADERS.get(ext)
    if not loader:
        raise ValueError(
            f"Unsupported file format: '{ext}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    doc = loader(path)
    if not doc.content:
        raise ValueError(f"Document is empty: {path.name}")
    return doc


def load_documents(directory: Path) -> list[Document]:
    """Load all supported documents from a directory.

    Uses the strategy pattern — each extension maps to its own loader.
    Unsupported formats are silently skipped.
    """
    documents = []
    if not directory.exists():
        raise FileNotFoundError(f"Documents directory not found: {directory}")

    for file_path in sorted(directory.iterdir()):
        ext = file_path.suffix.lower()
        loader = LOADERS.get(ext)
        if loader:
            print(f"  Loading [{ext}] {file_path.name}")
            try:
                doc = loader(file_path)
                if doc.content:
                    documents.append(doc)
                else:
                    print(f"  ⚠ Skipping empty document: {file_path.name}")
            except Exception as e:
                print(f"  ✗ Error loading {file_path.name}: {e}")
        else:
            print(f"  ⊘ Skipping unsupported format: {file_path.name}")

    return documents
