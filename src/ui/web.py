"""FastAPI web server — serves the chat UI and API endpoints."""

import shutil
import tempfile
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path

from src.agent.orchestrator import Orchestrator
from src.ingestion.ingest import ingest_single_file, ingest_all
from src.ingestion.loader import SUPPORTED_EXTENSIONS
from src.retrieval.vector_store import get_vector_store

app = FastAPI(title="Trenkwalder HR Chatbot", version="1.0.0")

templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

agent = Orchestrator()


@app.on_event("startup")
async def startup_ingest():
    """Ensure base company documents are in the vector store on startup."""
    store = get_vector_store()
    if store.count == 0:
        try:
            ingest_all()
        except Exception as e:
            print(f"⚠ Auto-ingestion failed: {e}")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        response = agent.chat(req.message)
        return ChatResponse(response=response)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Save an uploaded file, run it through the ingestion pipeline, and index it."""
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported file type: '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"},
        )

    dest_path = UPLOAD_DIR / filename
    try:
        with open(dest_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to save file: {e}"})

    try:
        result = ingest_single_file(dest_path)
        title = Path(filename).stem
        agent.set_last_uploaded(filename=filename, title=title)
        return {"status": "ok", "message": f"✅ '{filename}' uploaded and processed!", "details": result}
    except Exception as e:
        dest_path.unlink(missing_ok=True)
        return JSONResponse(status_code=500, content={"error": f"Ingestion failed: {e}"})


@app.get("/api/documents")
async def list_documents():
    """Return the list of uploaded documents and total chunk count."""
    documents = []
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
    return {"documents": documents, "total_chunks_in_store": store.count}


@app.post("/api/reset")
async def reset():
    """Reset conversation and uploads, but keep base company documents."""
    agent.reset()

    store = get_vector_store()
    removed = store.clear_all()

    # Delete uploaded files
    deleted_files = 0
    if UPLOAD_DIR.exists():
        for f in UPLOAD_DIR.iterdir():
            if f.is_file():
                f.unlink(missing_ok=True)
                deleted_files += 1

    # Re-ingest base company documents so the bot still knows about policies
    try:
        ingest_all()
    except Exception:
        pass

    return {
        "status": "ok",
        "message": "Conversation and uploads reset — base documents reloaded",
        "details": {"chunks_removed": removed, "files_deleted": deleted_files},
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "trenkwalder-chatbot"}
