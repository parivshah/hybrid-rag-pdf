from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    use_rerank: bool = True


class SourceSnippet(BaseModel):
    rank: int
    source: str
    chunk_index: int
    semantic_rank: int | None = None
    bm25_score: float | None = None
    distance: float | None = None
    excerpt: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceSnippet]
    grounded: bool
    refused: bool
    use_rerank: bool


class IngestResponse(BaseModel):
    filename: str
    chunks_indexed: int
    total_chunks: int
    bm25_documents: int


class StatusResponse(BaseModel):
    chunk_count: int
    bm25_documents: int
    sources: list[str]
    embed_model: str
    llm_model: str
    retrieval_candidates: int
    top_k: int


class ResetResponse(BaseModel):
    chunks_removed: int
