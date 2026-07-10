import ollama

from rag.anti_hallucination import REFUSAL_MESSAGE, assess_relevance
from rag.bm25_index import BM25Index
from rag.config import LLM_MODEL, MAX_EXCERPT_CHARS, TOP_K
from rag.retriever import retrieve
from rag.vector_store import VectorStore

SYSTEM_PROMPT = """You are a document Q&A assistant.
Answer questions using ONLY the provided document excerpts.
Cite section numbers and source filenames when possible.
If the answer is not stated in the excerpts, respond with exactly:
"I cannot answer that based on the document."
Do not use outside knowledge. Do not guess or invent facts.
Keep answers concise and practical."""


def _truncate(text: str, max_chars: int = MAX_EXCERPT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def build_prompt(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return question

    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(f"[{i}] (source: {chunk['source']})\n{chunk['text']}")

    context = "\n\n".join(context_parts)
    return f"""Policy excerpts:
{context}

Question: {question}

Answer based on the policy excerpts above:"""


def format_sources(chunks: list[dict]) -> list[dict]:
    sources = []
    for i, chunk in enumerate(chunks, start=1):
        sources.append(
            {
                "rank": i,
                "source": chunk["source"],
                "chunk_index": chunk["chunk_index"],
                "semantic_rank": chunk.get("semantic_rank"),
                "bm25_score": chunk.get("bm25_score"),
                "distance": round(chunk["distance"], 4) if chunk.get("distance") is not None else None,
                "excerpt": _truncate(chunk["text"]),
            }
        )
    return sources


def generate_answer(question: str, chunks: list[dict]) -> str:
    user_prompt = build_prompt(question, chunks)
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response["message"]["content"]


def ask(
    question: str,
    store: VectorStore,
    bm25: BM25Index,
    *,
    top_k: int = TOP_K,
    use_rerank: bool = True,
) -> dict:
    chunks = retrieve(question, store, bm25, top_k=top_k, use_rerank=use_rerank)
    relevant, refusal = assess_relevance(chunks)

    if not relevant:
        return {
            "question": question,
            "answer": refusal or REFUSAL_MESSAGE,
            "sources": format_sources(chunks),
            "grounded": False,
            "refused": True,
            "use_rerank": use_rerank,
        }

    answer = generate_answer(question, chunks)
    refused = "cannot answer" in answer.lower()
    return {
        "question": question,
        "answer": answer,
        "sources": format_sources(chunks),
        "grounded": not refused,
        "refused": refused,
        "use_rerank": use_rerank,
    }
