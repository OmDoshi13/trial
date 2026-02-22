# Trenkwalder AI HR Chatbot

An AI-powered HR assistant chatbot built with **RAG (Retrieval-Augmented Generation)** that answers questions from company documents (PDF, TXT, Markdown) and fetches real-time employee data via tool/function calling — all running **100% locally** using Ollama.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│           Web UI (FastAPI + HTML/JS/CSS)             │
│         http://localhost:8000                        │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              Agent Orchestrator                       │
│   • Intent detection (HR query vs document query)    │
│   • LLM-based tool calling (TOOL_CALL: ...)         │
│   • Conversation history management                  │
│   • Pre-emptive document search for context          │
└──────┬──────────────────────────────┬───────────────┘
       │                              │
       ▼                              ▼
┌──────────────────┐        ┌──────────────────────┐
│  RAG Pipeline     │        │   HR Tool Functions   │
│  • PDF/TXT/MD     │        │   (Mock HR API)       │
│    ingestion      │        │   Port 8001            │
│  • Text chunking  │        │                        │
│  • Embedding via   │        │  • get_vacation_days  │
│    nomic-embed-text│        │  • get_sick_leave     │
│  • ChromaDB vector │        │  • get_upcoming_leave │
│    store           │        │  • get_employee_profile│
│  • Semantic search │        │  • get_payslip_info   │
└──────────────────┘        └──────────────────────┘
       │                              │
       └─────────────┬────────────────┘
                     ▼
           ┌──────────────────┐
           │  Ollama (Local)   │
           │  • llama3.2 (LLM) │
           │  • nomic-embed-text│
           │    (Embeddings)    │
           └──────────────────┘
```

## ✨ Features

### Core Capabilities
- **Document Q&A (RAG)**: Upload and query PDF, TXT, and Markdown documents
- **Dynamic HR Data**: Real-time employee information via mock HR API (vacation days, sick leave, payslip, profile)
- **Smart Intent Detection**: Automatically routes questions to document search or HR tools based on keywords
- **Tool Calling**: LLM decides when to call external tools using `TOOL_CALL:` pattern
- **Conversation Memory**: Maintains chat history within a session for contextual follow-ups

### Document Support
- **Company documents auto-ingested** on startup from `documents/` folder
- **Runtime document upload** via the web UI (PDF, TXT, MD)
- **Semantic search** — finds relevant content even when exact keywords don't match
- **Multi-document support** — query across all uploaded documents simultaneously

### Web UI
- Modern dark-themed chat interface
- **Upload Doc** button for runtime document ingestion
- **Documents** sidebar showing all ingested documents
- **New Chat** button to reset conversation and start fresh
- Real-time typing indicator while processing
- Markdown rendering in bot responses

### HR Tools (Mock API)
| Tool | Description | Example Query |
|------|-------------|---------------|
| `get_vacation_days` | PTO/vacation balance | "How many vacation days do I have?" |
| `get_sick_leave` | Sick leave balance | "What's my sick leave balance?" |
| `get_upcoming_leave` | Scheduled future leave | "Do I have any upcoming leave?" |
| `get_employee_profile` | Employee info (name, dept, manager) | "What's my employee profile?" |
| `get_payslip_info` | Salary and payslip details | "What is the salary of Om Doshi?" |

### Employee Mapping
| Name | Employee ID |
|------|-------------|
| Om Doshi | EMP001 (default) |
| Klahm Sebestian | EMP002 |

## 📋 Prerequisites

- **Python 3.11+**
- **Ollama** installed and running locally ([install here](https://ollama.com))

## 🚀 Quick Start

### 1. Install Ollama & pull models

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama
ollama serve

# Pull required models
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 2. Setup the project

```bash
# Clone and navigate to project
cd trenkwalder-chatbot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env
```

### 3. Run the chatbot

**Web UI (recommended):**
```bash
python3 -m src.main web
```
- Chat UI: http://localhost:8000
- Mock HR API: http://localhost:8001 (started automatically)

**CLI mode:**
```bash
python3 -m src.main cli
```

**Ingest documents only:**
```bash
python3 -m src.main ingest
```

## 📁 Project Structure

```
trenkwalder-chatbot/
├── documents/                  # Company documents (auto-ingested on startup)
│   ├── company_overview.md
│   ├── employee_benefits.md
│   ├── faq.md
│   ├── it_security_policy.md
│   └── onboarding_guide.md
├── src/
│   ├── agent/
│   │   ├── orchestrator.py     # Core agent — intent detection, tool calling, RAG
│   │   └── prompts.py          # System prompt & answer templates
│   ├── ingestion/
│   │   ├── chunker.py          # Text chunking (500 chars, 50 overlap)
│   │   ├── embedder.py         # Ollama embedding generation
│   │   ├── ingest.py           # Document ingestion pipeline
│   │   └── loaders.py          # PDF, TXT, MD file loaders
│   ├── retrieval/
│   │   └── vector_store.py     # ChromaDB vector store + semantic search
│   ├── tools/
│   │   ├── hr_tools.py         # HR tool function definitions
│   │   └── mock_hr_service.py  # FastAPI mock HR API (port 8001)
│   ├── ui/
│   │   ├── cli.py              # Terminal chat interface
│   │   └── web.py              # FastAPI web app + API endpoints
│   ├── config.py               # Pydantic settings (env-based config)
│   └── main.py                 # Entry point (web/cli/ingest commands)
├── templates/
│   └── index.html              # Web UI (HTML + CSS + JS, single file)
├── tests/
│   └── __init__.py
├── chroma_data/                # ChromaDB persistent storage (auto-created)
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 How It Works

### 1. Document Ingestion
```
PDF/TXT/MD files → Loader → Text Chunks (500 chars) → Embeddings (nomic-embed-text) → ChromaDB
```
- Documents in `documents/` are auto-ingested when the server starts
- Users can upload additional documents at runtime via the web UI

### 2. Query Processing
```
User Question
     │
     ▼
Intent Detection (keyword-based)
     │
     ├── HR Question? ──→ Skip doc search, let LLM call HR tools
     │
     ├── Document Question? ──→ Pre-emptive semantic search in ChromaDB
     │                          Attach top 5 chunks as context
     │
     └── General/Greeting? ──→ LLM responds directly
     │
     ▼
LLM (llama3.2) generates response
     │
     ├── TOOL_CALL detected? ──→ Execute tool → Feed result back to LLM
     │
     └── Direct answer ──→ Return to user
```

### 3. Tool Calling Flow
```
User: "What is the salary of Om Doshi?"
  → Orchestrator detects HR keywords ("salary", "Om Doshi")
  → Skips document search
  → LLM receives system prompt with employee mapping (Om Doshi → EMP001)
  → LLM outputs: TOOL_CALL: get_payslip_info(employee_id="EMP001")
  → Orchestrator calls Mock HR API: GET http://localhost:8001/api/payslip/EMP001
  → Result fed back to LLM
  → LLM generates human-friendly answer with salary details
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM | Ollama + llama3.2 | Text generation, tool calling |
| Embeddings | Ollama + nomic-embed-text | Semantic text embeddings |
| Vector Store | ChromaDB | Document storage & similarity search |
| Web Framework | FastAPI | REST API + web UI serving |
| Frontend | HTML + CSS + Vanilla JS | Single-file chat interface |
| CLI | Typer + Rich | Terminal interface |
| Config | Pydantic Settings | Type-safe environment configuration |
| HTTP Client | httpx | Async API calls to Ollama & HR service |
| PDF Parsing | PyMuPDF (fitz) | PDF text extraction |

## 🎯 Design Decisions

1. **Fully local with Ollama** — No cloud API keys needed, all data stays on-device
2. **ChromaDB** — Lightweight persistent vector store, ideal for local development
3. **LLM-driven tool calling** — The LLM decides when to call tools via `TOOL_CALL:` pattern in system prompt; no hard-coded if/else routing
4. **Keyword-based intent pre-filtering** — HR keywords skip document search to avoid irrelevant context polluting tool-call decisions
5. **Strategy pattern for loaders** — Each document format (PDF, TXT, MD) has its own loader; easy to add new formats
6. **Single-file frontend** — All HTML, CSS, and JS in one `index.html` for simplicity
7. **Mock HR service as separate FastAPI app** — Runs on port 8001, simulates a real microservice architecture
8. **Pydantic Settings for config** — Type-safe, environment-variable-based configuration with `.env` support

## 📝 Assumptions

- Ollama is running locally on port 11434
- Company documents are in the `documents/` directory
- Mock HR data covers two employees: EMP001 (Om Doshi) and EMP002 (Klahm Sebestian)
- Single-user chatbot (no authentication)
- Conversation history is session-based (resets on server restart or "New Chat")

## 🚧 What I'd Improve With More Time

- **Streaming responses** (SSE) for real-time token-by-token output
- **Persistent chat history** with session management
- **Multi-user support** with authentication
- **Docker containerization** for one-command deployment
- **RAG evaluation** using RAGAS framework
- **Caching layer** for repeated queries
- **Observability** with OpenTelemetry tracing
- **Real HR API integration** replacing mock service
- **Cloud deployment** (AWS Lambda + API Gateway + S3 + RDS)
- **Unit & integration tests** with pytest
- **Document deletion** from the vector store
- **Hybrid search** combining semantic + keyword (BM25) retrieval