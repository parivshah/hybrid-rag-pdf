# Talk to your PDF — Hybrid RAG Challenge

A full-stack **Talk to your PDF** app built with **Python (FastAPI)**, **React**, **Ollama** (`llama3` + `nomic-embed-text`), **ChromaDB**, and **BM25 reranking**.

## Features

- **PDF upload** via React UI → Python REST API → text extraction → recursive chunking → embeddings → ChromaDB
- **Hybrid retrieval**: semantic search (top-20) → **BM25 rerank** → top-k chunks to LLM
- **Grounded answers** with visible source excerpts (semantic rank, BM25 score, distance)
- **Anti-hallucination**: relevance gates on retrieval scores + strict LLM prompt; out-of-scope questions are declined
- **Clear layers**: `ingest_service` / `retriever` / `chat_service` + CLI still available

## Stack choice (vs suggested C#/.NET)

| Layer | Choice | Why |
|-------|--------|-----|
| API | FastAPI | Fast to wire, async upload, OpenAPI docs |
| UI | React + Vite | Matches React requirement |
| LLM | Ollama `llama3` | Fully local, no API keys |
| Embeddings | Ollama `nomic-embed-text` | Local, good quality/size tradeoff |
| Vector DB | ChromaDB (persistent) | Zero-config local store |
| Reranking | rank-bm25 | Exact-term recall on policy language |

## Prerequisites

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com/) running locally

```bash
ollama pull llama3
ollama pull nomic-embed-text
```

## Setup

### Backend

```bash
cd hybrid-rag-pdf
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Run (web demo)

**Terminal 1 — API** (from project root):

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — React** (from `frontend/`):

```bash
npm run dev
```

Open http://localhost:5173

1. Upload `data/sample-policy.pdf` (or any text-based PDF)
2. Ask 2–3 in-document questions (e.g. deductible, coverage exclusions)
3. Ask an out-of-scope question (e.g. "What is the capital of France?") — should be **declined**

API docs: http://127.0.0.1:8000/docs

## CLI (optional)

```bash
python main.py ingest data/sample-policy.pdf
python main.py ask "What is my wind/hail deductible?" --show-sources
python main.py search "mold coverage" --no-rerank
python main.py status
```

## Architecture

```
React UI
  │  POST /api/documents/upload
  │  POST /api/chat/ask
  ▼
FastAPI (api/main.py)
  ├── IngestService  → PDF → chunk → embed → ChromaDB + BM25 index
  └── ChatService    → retrieve → anti-hallucination gate → Ollama llama3

Retrieval pipeline:
  Question → semantic top-20 (Chroma) → BM25 rerank → top-4 → LLM
```

## Configuration (`rag/config.py`)

| Setting | Default | Purpose |
|---------|---------|---------|
| `LLM_MODEL` | `llama3` | Ollama chat model |
| `EMBED_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `CHUNK_SIZE` | `500` | Recursive chunk target (chars) |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `RETRIEVAL_CANDIDATES` | `20` | Semantic pool before BM25 |
| `TOP_K` | `4` | Chunks sent to LLM |
| `MAX_SEMANTIC_DISTANCE` | `0.85` | Anti-hallucination: max L2 distance |
| `MIN_BM25_SCORE` | `1.0` | Anti-hallucination: min BM25 score |

### Tuning tradeoffs

- **Smaller chunks** (300–400): better precision, more index size
- **Larger top-k** (6–8): more context for complex questions, more LLM tokens
- **Lower `MAX_SEMANTIC_DISTANCE`**: stricter refusal (fewer hallucinations, more false declines)
- **BM25 rerank**: helps exact terms ("deductible", section numbers); disable with `use_rerank: false`

## Anti-hallucination

1. **Retrieval gate**: if best semantic distance or BM25 scores are below thresholds, return a polite refusal **without** calling the LLM
2. **Prompt constraint**: LLM instructed to answer only from excerpts and say it cannot answer otherwise
3. **Post-check**: LLM responses containing "cannot answer" are flagged as `refused: true`

## Project layout

```
hybrid-rag-pdf/
├── api/                 # FastAPI REST layer
├── frontend/            # React SPA
├── rag/                 # Core RAG (ingest, retrieve, answer)
│   ├── services/
│   ├── anti_hallucination.py
│   └── ...
├── main.py              # CLI
├── data/sample-policy.pdf
└── requirements.txt
```

## Production hardening (next steps)

- Auth + rate limiting on upload/ask endpoints
- Azure Container Apps / App Service deployment with Ollama sidecar or managed embeddings
- Automated retrieval eval tests (pytest + golden Q&A set)
- OCR for scanned PDFs (e.g. Tesseract / Azure Document Intelligence)

## AI tooling used

Built with Cursor agent assistance. Verify manually: upload flow, 3 grounded Q&As, 1 out-of-scope decline, source snippets visible.

## Limitations

- Text-based PDFs only (no OCR)
- Single-machine, fully local
- No conversation memory or streaming
