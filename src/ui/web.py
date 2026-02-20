"""FastAPI web interface for the chatbot."""

import shutil
import tempfile
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path

from src.agent.orchestrator import Orchestrator
from src.ingestion.ingest import ingest_single_file
from src.ingestion.loader import SUPPORTED_EXTENSIONS
from src.retrieval.vector_store import get_vector_store

app = FastAPI(title="Trenkwalder HR Chatbot", version="1.0.0")

# Templates
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Static files
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Upload directory for persisting uploaded files
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Agent instance (per-process; for production you'd want session-based)
agent = Orchestrator()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main chat UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Handle a chat message and return the response."""
    try:
        response = agent.chat(req.message)
        return ChatResponse(response=response)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document (PDF, TXT, or MD) and ingest it into the knowledge base.

    The file is saved to the uploads/ directory, then processed through
    the ingestion pipeline (load → chunk → embed → store in ChromaDB).
    """
    # Validate file extension
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Unsupported file type: '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            },
        )

    # Save uploaded file
    dest_path = UPLOAD_DIR / filename
    try:
        with open(dest_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to save file: {e}"})

    # Ingest into vector store
    try:
        result = ingest_single_file(dest_path)

        # Tell the orchestrator which document was just uploaded so that
        # subsequent questions like "tell me about the document" resolve
        # to THIS file rather than an older upload.
        title = Path(filename).stem  # matches the title used by the ingestion pipeline
        agent.set_last_uploaded(filename=filename, title=title)

        return {
            "status": "ok",
            "message": f"✅ '{filename}' uploaded and processed successfully!",
            "details": result,
        }
    except Exception as e:
        # Clean up on failure
        dest_path.unlink(missing_ok=True)
        return JSONResponse(status_code=500, content={"error": f"Ingestion failed: {e}"})


@app.get("/api/documents")
async def list_documents():
    """List uploaded documents in the knowledge base."""
    documents = []

    # Only show uploaded documents (not pre-loaded/built-in ones)
    if UPLOAD_DIR.exists():
        for f in sorted(UPLOAD_DIR.iterdir()):
            if f.suffix.lower() in SUPPORTED_EXTENSIONS:
                documents.append({
                    "name": f.name,
                    "format": f.suffix.lower().lstrip("."),
                    "type": "uploaded",
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })

    store = get_vector_store()
    return {
        "documents": documents,
        "total_chunks_in_store": store.count,
    }


@app.post("/api/reset")
async def reset():
    """Reset the conversation history."""
    agent.reset()
    return {"status": "ok", "message": "Conversation reset"}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "trenkwalder-chatbot"}
