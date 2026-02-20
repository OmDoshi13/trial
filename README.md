# Trenkwalder AI Chatbot

A simple, modular chatbot that answers questions from static multi-modal documents (PDF, TXT, Markdown) using RAG (Retrieval-Augmented Generation) and fetches dynamic information from external services via tool/function calling.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Web UI (FastAPI + HTML/JS)          │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│            Agent Orchestrator                     │
│   (Intent routing via LLM tool-calling)          │
└──────┬─────────────────────────┬────────────────┘
       │                         │
       ▼                         ▼
┌──────────────┐        ┌──────────────────┐
│ RAG Pipeline  │        │  Tool Functions   │
│ ChromaDB +    │        │  (Mock HR APIs)   │
│ Embeddings    │        │  vacation, sick   │
│ + LLM         │        │  leave, payslip   │
└──────────────┘        └──────────────────┘
       │                         │
       └────────────┬────────────┘
                    ▼
          ┌──────────────────┐
          │  Ollama (Local)   │
          │  llama3.2 + embed │
          └──────────────────┘
```

## Features

- **Multi-format document ingestion**: PDF, TXT, Markdown
- **RAG pipeline**: ChromaDB vector store + Ollama embeddings + LLM answer generation
- **Dynamic tool calling**: Simulated HR services (vacation days, sick leave, employee profile, payslips)
- **Dual interface**: CLI + Web UI
- **Fully local**: Runs entirely on your machine via Ollama (no cloud API keys needed)

## Prerequisites

- **Python 3.11+**
- **Ollama** installed and running locally ([install here](https://ollama.com))

## Quick Start

### 1. Install Ollama & pull models

```bash
# Install Ollama (if not already)
brew install ollama  # macOS

# Start Ollama
ollama serve

# Pull required models
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 2. Setup the project

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env
```

### 3. Ingest documents

```bash
python -m src.ingestion.ingest
```

### 4. Run the chatbot

**Web UI (recommended):**
```bash
python -m src.main web
```
Then open http://localhost:8000 in your browser.

**CLI mode:**
```bash
python -m src.main cli
```

## Project Structure

```
trenkwalder-chatbot/
├── documents/              # Static content (PDF, TXT, MD)
├── src/
│   ├── ingestion/          # Document loading, chunking, embedding
│   ├── retrieval/          # Vector store & similarity search
│   ├── tools/              # Mock external HR services
│   ├── agent/              # LLM orchestrator & prompt templates
│   ├── ui/                 # CLI and Web interfaces
│   ├── config.py           # Centralized configuration
│   └── main.py             # Application entry point
├── tests/                  # Unit tests
├── static/                 # Web UI assets
├── templates/              # HTML templates
└── requirements.txt
```

## Design Decisions

1. **Ollama for fully local inference** — No cloud dependencies, data stays on-device
2. **ChromaDB** — Lightweight, persistent vector store, perfect for local dev
3. **Tool-calling pattern** — The LLM decides when to call tools based on system prompt and user intent; no manual if/else routing
4. **Strategy pattern for loaders** — Each document format has its own loader; easy to extend
5. **Pydantic for config** — Type-safe configuration with validation
6. **FastAPI for web** — Modern async web framework with auto-generated docs

## Assumptions

- Ollama is running locally on port 11434
- Documents are placed in the `documents/` directory before ingestion
- Mock HR data simulates a single employee ("EMP001") for demo purposes
- The chatbot is single-user for simplicity

## What I'd Improve With More Time

- Streaming responses (SSE) for better UX
- Conversation memory / history persistence
- Multi-user support with authentication
- Real AWS deployment (Lambda + API Gateway + S3)
- RAG evaluation framework (RAGAS)
- Caching layer for repeated queries
- Observability & tracing (OpenTelemetry)
- Docker containerization for one-command setup
