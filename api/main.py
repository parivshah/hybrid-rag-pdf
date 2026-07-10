"""FastAPI REST API for Talk-to-your-PDF RAG."""

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import AskRequest, AskResponse, IngestResponse, ResetResponse, StatusResponse
from rag.bm25_index import BM25Index
from rag.config import TOP_K
from rag.services.chat_service import ChatService
from rag.services.ingest_service import IngestService

app = FastAPI(
    title="Talk to your PDF",
    description="Upload a PDF, index with hybrid retrieval (semantic + BM25), ask questions via Ollama.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ingest_service = IngestService()
chat_service = ChatService(store=ingest_service.store)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return StatusResponse(**ingest_service.status())


@app.post("/api/documents/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    reset: bool = False,
) -> IngestResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = file.filename.lower().rsplit(".", 1)[-1]
    if suffix not in {"pdf", "txt"}:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        saved = ingest_service.save_upload(file.filename, content)
        result = ingest_service.ingest_file(saved, reset=reset)
        chat_service.bm25 = BM25Index.load()
        return IngestResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/chat/ask", response_model=AskResponse)
def ask_question(body: AskRequest) -> AskResponse:
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = chat_service.ask_question(
            question,
            top_k=body.top_k or TOP_K,
            use_rerank=body.use_rerank,
        )
        return AskResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/api/documents", response_model=ResetResponse)
def reset_documents() -> ResetResponse:
    result = ingest_service.reset()
    chat_service.bm25 = BM25Index.load()
    return ResetResponse(**result)
