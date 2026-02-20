"""Agent orchestrator — the brain of the chatbot.

Handles the full conversation flow:
1. Sends user message + system prompt to LLM
2. Parses LLM response for tool calls
3. Executes tools (including RAG document search)
4. Sends tool results back to LLM for final answer

Key design: every user question that might relate to documents automatically
triggers a vector search so the LLM always has context from the knowledge base.
"""

import re
import json
from datetime import date
from pathlib import Path
import httpx

from src.config import settings
from src.agent.prompts import SYSTEM_PROMPT, ANSWER_WITH_CONTEXT_PROMPT
from src.tools.registry import execute_tool, TOOL_FUNCTIONS
from src.retrieval.vector_store import get_vector_store

# Directories where documents live
_DOCS_DIR = Path(__file__).parent.parent.parent / "documents"
_UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
_SUPPORTED = {".pdf", ".txt", ".md"}


def _list_all_document_names() -> list[str]:
    """Return the filenames of every document in the knowledge base."""
    names: list[str] = []
    for folder in (_DOCS_DIR, _UPLOAD_DIR):
        if folder.exists():
            for f in sorted(folder.iterdir()):
                if f.suffix.lower() in _SUPPORTED:
                    names.append(f.name)
    return names


# Simple keyword heuristics to decide if a message is about document content
_DOC_KEYWORDS = [
    "document", "file", "uploaded", "pdf", "resume", "cv", "report",
    "skills", "experience", "education", "qualifications", "summary",
    "summarize", "extract", "list", "mention", "mentioned", "content",
    "policy", "benefit", "onboarding", "faq", "guide", "procedure",
    "what does", "what is", "tell me about", "information",
]


def _looks_like_document_question(text: str) -> bool:
    """Return True if the user message likely concerns document content."""
    lower = text.lower()
    # Very short greetings are not document questions
    if len(lower.split()) <= 2 and any(w in lower for w in ("hi", "hello", "hey", "thanks", "bye")):
        return False
    # Check for keyword overlap
    return any(kw in lower for kw in _DOC_KEYWORDS)


class Orchestrator:
    """Main chatbot orchestrator that coordinates LLM, tools, and RAG."""

    def __init__(self):
        self.conversation_history: list[dict] = []
        # Tracks the most recently uploaded document in this session so
        # that vague references like "the document" resolve correctly.
        self._last_uploaded_title: str | None = None
        self._last_uploaded_filename: str | None = None

    def set_last_uploaded(self, filename: str, title: str) -> None:
        """Called by the upload endpoint after a successful ingestion."""
        self._last_uploaded_filename = filename
        self._last_uploaded_title = title

    # ------------------------------------------------------------------
    # Dynamic system prompt — rebuilt on every call so uploaded docs are
    # always listed and the *current* document is highlighted.
    # ------------------------------------------------------------------
    def _build_system_prompt(self) -> str:
        """Build the system prompt with the current list of documents."""
        doc_names = _list_all_document_names()
        parts: list[str] = []
        if doc_names:
            doc_list = "\n".join(f"  - {name}" for name in doc_names)
            parts.append(
                f"\n## Documents currently in the knowledge base:\n{doc_list}\n"
                "If the user asks about ANY of these documents, you MUST call "
                "search_documents with a relevant query."
            )
        if self._last_uploaded_filename:
            parts.append(
                f"\n## MOST RECENTLY UPLOADED DOCUMENT (this session): "
                f"{self._last_uploaded_filename}\n"
                "When the user says 'the document', 'the uploaded file', 'the PDF', "
                "or asks a question without specifying which document, they are "
                f"referring to **{self._last_uploaded_filename}**. "
                "Focus your answer on this document's content."
            )
        uploaded_docs_context = "\n".join(parts)

        return SYSTEM_PROMPT.format(
            current_date=str(date.today()),
            uploaded_docs_context=uploaded_docs_context,
        )

    def _call_llm(self, messages: list[dict]) -> str:
        """Call Ollama's chat API."""
        response = httpx.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.llm_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1024,
                },
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    def _parse_tool_calls(self, response: str) -> list[dict]:
        """Parse TOOL_CALL directives from LLM response.

        Expected format: TOOL_CALL: tool_name(param1="value1", param2="value2")
        """
        tool_calls = []
        pattern = r'TOOL_CALL:\s*(\w+)\(([^)]*)\)'
        matches = re.findall(pattern, response)

        for name, args_str in matches:
            # Parse the arguments
            arguments = {}
            if args_str.strip():
                # Match key="value" pairs
                arg_pattern = r'(\w+)\s*=\s*"([^"]*)"'
                arg_matches = re.findall(arg_pattern, args_str)
                for key, value in arg_matches:
                    arguments[key] = value

            tool_calls.append({"name": name, "arguments": arguments})

        return tool_calls

    def _execute_document_search(self, query: str, n_results: int = 5) -> str:
        """Execute RAG document search.

        Search strategy (in priority order):
        1. If a document was recently uploaded in this session, search
           specifically within that document's chunks first.
        2. Also search across all uploaded documents.
        3. Also search across the full knowledge base.
        Results are merged with the current-document chunks first.
        """
        store = get_vector_store()

        # --- Priority 1: search within the CURRENT (last-uploaded) document ---
        current_doc_results: list[dict] = []
        if self._last_uploaded_title:
            try:
                current_doc_results = store.query(
                    query_text=query,
                    n_results=n_results,
                    where={"title": self._last_uploaded_title},
                )
            except Exception:
                pass

        # --- Priority 2: search all uploaded documents ---
        uploaded_results: list[dict] = []
        lower_q = query.lower()
        upload_keywords = ["upload", "document", "file", "pdf", "cv", "resume", "report"]
        if any(kw in lower_q for kw in upload_keywords) or self._last_uploaded_title:
            try:
                uploaded_results = store.query(
                    query_text=query,
                    n_results=n_results,
                    where={"uploaded": "true"},
                )
            except Exception:
                pass

        # --- Priority 3: general search across all documents ---
        general_results = store.query(query_text=query, n_results=n_results)

        # Merge with deduplication: current doc first, then other uploads, then general
        seen_texts: set[str] = set()
        merged: list[dict] = []
        for r in current_doc_results + uploaded_results + general_results:
            if r["text"] not in seen_texts:
                seen_texts.add(r["text"])
                merged.append(r)

        results = merged[: n_results + 3]  # keep a few extra for quality

        if not results:
            return "No relevant documents found."

        context_parts = []
        for i, chunk in enumerate(results):
            source = chunk["metadata"].get("title", "unknown")
            fmt = chunk["metadata"].get("format", "")
            context_parts.append(
                f"[Source: {source}.{fmt}]\n{chunk['text']}"
            )

        return "\n\n---\n\n".join(context_parts)

    def _execute_all_tools(self, tool_calls: list[dict]) -> str:
        """Execute all tool calls and format results."""
        results = []
        for tc in tool_calls:
            name = tc["name"]
            args = tc["arguments"]

            if name == "search_documents":
                # Be lenient: accept "query" key, or fall back to the first
                # value the LLM provided (it sometimes uses "param1" etc.)
                query = args.get("query") or next(iter(args.values()), "")
                if not query:
                    continue  # skip empty search — pre-emptive search covers it
                result = self._execute_document_search(query)
                results.append(f"📄 Document Search Results for '{query}':\n{result}")
            else:
                result = execute_tool(name, args)
                results.append(f"🔧 {name} result:\n{result}")

        return "\n\n".join(results)

    def chat(self, user_message: str) -> str:
        """Process a user message and return the chatbot's response.

        Flow:
        1. Build an up-to-date system prompt (includes uploaded file names)
        2. If the message looks document-related, proactively search the
           knowledge base so we always have context regardless of whether
           the LLM emits a TOOL_CALL.
        3. Send message to LLM with system prompt
        4. Parse any additional TOOL_CALL directives and execute them
        5. Combine all context and ask the LLM for a final answer
        """
        # 0. Fresh system prompt with current docs list
        system_prompt = self._build_system_prompt()

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # ------------------------------------------------------------------
        # 1. PRE-EMPTIVE document search — the key reliability improvement.
        #    If the user's question looks like it's about document content,
        #    we run a vector search NOW so the LLM always has that context,
        #    even if it forgets to emit TOOL_CALL: search_documents.
        # ------------------------------------------------------------------
        preemptive_context: str | None = None
        if _looks_like_document_question(user_message):
            preemptive_context = self._execute_document_search(user_message)

        # Build messages for LLM
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history[-10:],  # Keep last 10 messages for context
        ]

        # Step 2: Get LLM's initial response (may contain tool calls)
        llm_response = self._call_llm(messages)

        # Step 3: Check for tool calls
        tool_calls = self._parse_tool_calls(llm_response)

        # ------------------------------------------------------------------
        # 2. Collect ALL context — from pre-emptive search AND tool calls.
        #    Always include pre-emptive results when we have a current doc
        #    because the LLM's own tool call may be malformed / wrong query.
        # ------------------------------------------------------------------
        all_context_parts: list[str] = []

        # Add pre-emptive search results
        if preemptive_context:
            all_context_parts.append(
                f"📄 Document Search Results (auto):\n{preemptive_context}"
            )

        # Execute any explicit tool calls from the LLM (excluding search_documents
        # if we already did a pre-emptive search, to avoid duplicate noise)
        if tool_calls:
            if preemptive_context:
                # Filter out search_documents calls — we already searched
                non_search_calls = [tc for tc in tool_calls if tc["name"] != "search_documents"]
                if non_search_calls:
                    tool_results = self._execute_all_tools(non_search_calls)
                    all_context_parts.append(tool_results)
            else:
                tool_results = self._execute_all_tools(tool_calls)
                all_context_parts.append(tool_results)

        # ------------------------------------------------------------------
        # 3. If we have context from tools/search, ask LLM to synthesize a
        #    final answer grounded in the retrieved information.
        # ------------------------------------------------------------------
        if all_context_parts:
            combined_context = "\n\n".join(all_context_parts)

            # Prepend a note about the current document so the LLM knows
            # what "the document" refers to.
            if self._last_uploaded_filename:
                combined_context = (
                    f"⚡ The most recently uploaded document in this session is: "
                    f"**{self._last_uploaded_filename}** (title: {self._last_uploaded_title}). "
                    f"When the user refers to 'the document' or 'uploaded file', "
                    f"answer using content from this document.\n\n"
                    + combined_context
                )

            answer_messages = [
                {"role": "system", "content": (
                    "You are a helpful HR assistant. The user asked a question and "
                    "relevant documents have already been retrieved. Your job is to "
                    "answer the question based ONLY on the retrieved information. "
                    "Do NOT call any tools. Do NOT output TOOL_CALL. Just answer."
                )},
                {"role": "user", "content": ANSWER_WITH_CONTEXT_PROMPT.format(
                    context=combined_context,
                    question=user_message,
                )},
            ]

            final_response = self._call_llm(answer_messages)

            # Safety: strip any stray TOOL_CALL lines the LLM may still emit
            final_response = re.sub(r'TOOL_CALL:\s*\w+\([^)]*\)\s*', '', final_response).strip()

            self.conversation_history.append({"role": "assistant", "content": final_response})
            return final_response
        else:
            # No tool calls and no pre-emptive search — direct LLM response
            self.conversation_history.append({"role": "assistant", "content": llm_response})
            return llm_response

    def reset(self):
        """Clear conversation history and uploaded-document tracking."""
        self.conversation_history = []
        self._last_uploaded_title = None
        self._last_uploaded_filename = None
