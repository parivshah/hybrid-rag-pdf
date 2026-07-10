from rag.bm25_index import BM25Index
from rag.config import TOP_K
from rag.query import ask
from rag.vector_store import VectorStore


class ChatService:
    def __init__(self, store: VectorStore | None = None, bm25: BM25Index | None = None) -> None:
        self.store = store or VectorStore()
        self.bm25 = bm25 or BM25Index.load()

    def ask_question(
        self,
        question: str,
        *,
        top_k: int = TOP_K,
        use_rerank: bool = True,
    ) -> dict:
        if self.store.count() == 0:
            return {
                "question": question,
                "answer": "No document has been uploaded yet. Please upload a PDF first.",
                "sources": [],
                "grounded": False,
                "refused": True,
                "use_rerank": use_rerank,
            }

        return ask(
            question,
            self.store,
            self.bm25,
            top_k=top_k,
            use_rerank=use_rerank,
        )
