from rag.bm25_index import BM25Index
from rag.config import RETRIEVAL_CANDIDATES, TOP_K
from rag.vector_store import VectorStore


def retrieve(
    question: str,
    store: VectorStore,
    bm25: BM25Index,
    *,
    top_k: int = TOP_K,
    use_rerank: bool = True,
) -> list[dict]:
    candidates = store.query(question, top_k=RETRIEVAL_CANDIDATES)
    if not candidates:
        return []

    if not use_rerank or len(candidates) <= top_k:
        return [
            {**candidate, "semantic_rank": rank, "bm25_score": None}
            for rank, candidate in enumerate(candidates[:top_k], start=1)
        ]

    return bm25.rerank(question, candidates, top_k=top_k)
