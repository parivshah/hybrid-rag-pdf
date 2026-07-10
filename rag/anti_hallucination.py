"""Relevance gates so out-of-scope questions are declined instead of hallucinated."""

from rag.config import MAX_SEMANTIC_DISTANCE, MIN_BM25_SCORE, STRONG_SEMANTIC_DISTANCE

REFUSAL_MESSAGE = (
    "I cannot answer that question based on the uploaded document. "
    "The retrieved passages are not sufficiently relevant. "
    "Please ask something that is covered in the document."
)


def assess_relevance(
    chunks: list[dict],
    *,
    strong_distance: float = STRONG_SEMANTIC_DISTANCE,
    max_distance: float = MAX_SEMANTIC_DISTANCE,
    min_bm25: float = MIN_BM25_SCORE,
) -> tuple[bool, str]:
    if not chunks:
        return False, REFUSAL_MESSAGE

    distances = [chunk["distance"] for chunk in chunks if chunk.get("distance") is not None]
    best_distance = min(distances) if distances else float("inf")

    if best_distance <= strong_distance:
        return True, ""

    if best_distance > max_distance:
        return False, REFUSAL_MESSAGE

    bm25_scores = [chunk["bm25_score"] for chunk in chunks if chunk.get("bm25_score") is not None]
    if bm25_scores and max(bm25_scores) < min_bm25:
        return False, REFUSAL_MESSAGE

    return True, ""
