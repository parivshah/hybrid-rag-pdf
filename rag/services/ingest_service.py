import shutil
from pathlib import Path

from rag.bm25_index import BM25Index, rebuild_from_store
from rag.config import DATA_DIR, UPLOAD_DIR
from rag.document_loader import load_and_chunk
from rag.vector_store import VectorStore


class IngestService:
    def __init__(self, store: VectorStore | None = None) -> None:
        self.store = store or VectorStore()

    def ingest_file(self, path: Path, *, reset: bool = False) -> dict:
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = path.suffix.lower()
        if suffix not in {".pdf", ".txt"}:
            raise ValueError("Only .pdf and .txt files are supported")

        if reset:
            self.store.reset()
            BM25Index().reset()

        chunks = load_and_chunk(path)
        if not chunks:
            raise ValueError(f"No text could be extracted from {path.name}")

        count = self.store.add_chunks(path, chunks)
        bm25 = rebuild_from_store(self.store)

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        dest = DATA_DIR / path.name
        if path != dest.resolve():
            shutil.copy2(path, dest)

        return {
            "filename": path.name,
            "chunks_indexed": count,
            "total_chunks": self.store.count(),
            "bm25_documents": len(bm25.records),
        }

    def save_upload(self, filename: str, content: bytes) -> Path:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename).name
        dest = UPLOAD_DIR / safe_name
        dest.write_bytes(content)
        return dest

    def status(self) -> dict:
        from rag.config import EMBED_MODEL, LLM_MODEL, RETRIEVAL_CANDIDATES, TOP_K

        bm25 = BM25Index.load()
        return {
            "chunk_count": self.store.count(),
            "bm25_documents": len(bm25.records),
            "sources": self.store.list_sources(),
            "embed_model": EMBED_MODEL,
            "llm_model": LLM_MODEL,
            "retrieval_candidates": RETRIEVAL_CANDIDATES,
            "top_k": TOP_K,
        }

    def reset(self) -> dict:
        count = self.store.count()
        self.store.reset()
        BM25Index().reset()
        return {"chunks_removed": count}
