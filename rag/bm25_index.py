import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi

from rag.config import BM25_DIR


def tokenize(text: str) -> list[str]:
    return text.lower().split()


class BM25Index:
    def __init__(self) -> None:
        self.records: list[dict] = []
        self.bm25: BM25Okapi | None = None

    def build(self, records: list[dict]) -> None:
        if not records:
            self.records = []
            self.bm25 = None
            return

        self.records = records
        tokenized = [tokenize(record["text"]) for record in records]
        self.bm25 = BM25Okapi(tokenized)

    def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        if not candidates:
            return []

        if self.bm25 is None:
            return candidates[:top_k]

        query_tokens = tokenize(query)
        all_scores = self.bm25.get_scores(query_tokens)
        id_to_score = {record["id"]: all_scores[i] for i, record in enumerate(self.records)}

        reranked: list[dict] = []
        for semantic_rank, candidate in enumerate(candidates, start=1):
            chunk_id = candidate.get("id") or f"{candidate['source']}-{candidate['chunk_index']}"
            reranked.append(
                {
                    **candidate,
                    "semantic_rank": semantic_rank,
                    "bm25_score": round(float(id_to_score.get(chunk_id, 0.0)), 4),
                }
            )

        reranked.sort(key=lambda item: item["bm25_score"], reverse=True)
        return reranked[:top_k]

    def save(self, path: Path | None = None) -> Path:
        target = path or (BM25_DIR / "index.pkl")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as handle:
            pickle.dump({"records": self.records}, handle)
        return target

    @classmethod
    def load(cls, path: Path | None = None) -> "BM25Index":
        target = path or (BM25_DIR / "index.pkl")
        index = cls()
        if not target.exists():
            return index

        with target.open("rb") as handle:
            payload = pickle.load(handle)

        index.build(payload["records"])
        return index

    def reset(self) -> None:
        self.records = []
        self.bm25 = None
        index_path = BM25_DIR / "index.pkl"
        if index_path.exists():
            index_path.unlink()


def rebuild_from_store(store) -> BM25Index:
    records = store.get_all_chunks()
    index = BM25Index()
    index.build(records)
    if records:
        index.save()
    return index
