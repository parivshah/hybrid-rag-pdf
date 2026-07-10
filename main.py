#!/usr/bin/env python3
"""PolicyPulse — hybrid RAG CLI for insurance policy PDF Q&A."""

import argparse
import json
import shutil
import sys
from pathlib import Path

from rag.bm25_index import BM25Index, rebuild_from_store
from rag.config import DATA_DIR, EMBED_MODEL, LLM_MODEL, RETRIEVAL_CANDIDATES, TOP_K
from rag.document_loader import load_and_chunk
from rag.query import ask, format_sources
from rag.retriever import retrieve
from rag.vector_store import VectorStore


def cmd_ingest(args: argparse.Namespace) -> None:
    doc_path = Path(args.document).resolve()
    if not doc_path.exists():
        print(f"Error: file not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Ingesting {doc_path.name}...")
    chunks = load_and_chunk(doc_path)
    print(f"  Extracted {len(chunks)} text chunks")

    store = VectorStore()
    if args.reset:
        store.reset()
        BM25Index().reset()
        print("  Cleared existing vector store and BM25 index")

    count = store.add_chunks(doc_path, chunks)
    bm25 = rebuild_from_store(store)
    print(f"  Stored {count} vectors (total in DB: {store.count()})")
    print(f"  Rebuilt BM25 index ({len(bm25.records)} documents)")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dest = DATA_DIR / doc_path.name
    if doc_path != dest.resolve():
        shutil.copy2(doc_path, dest)
        print(f"  Copied document to {dest}")


def cmd_search(args: argparse.Namespace) -> None:
    store = VectorStore()
    if store.count() == 0:
        print("Error: no documents indexed. Run: python main.py ingest <your.pdf>", file=sys.stderr)
        sys.exit(1)

    bm25 = BM25Index.load()
    chunks = retrieve(
        args.question,
        store,
        bm25,
        top_k=args.top_k,
        use_rerank=not args.no_rerank,
    )
    result = {
        "question": args.question,
        "use_rerank": not args.no_rerank,
        "retrieval_candidates": RETRIEVAL_CANDIDATES,
        "top_k": args.top_k,
        "sources": format_sources(chunks),
    }
    print(json.dumps(result, indent=2))


def cmd_ask(args: argparse.Namespace) -> None:
    store = VectorStore()
    if store.count() == 0:
        print("Error: no documents indexed. Run: python main.py ingest <your.pdf>", file=sys.stderr)
        sys.exit(1)

    bm25 = BM25Index.load()
    print(
        f"Asking (index has {store.count()} chunks, "
        f"rerank={'on' if not args.no_rerank else 'off'})...\n"
    )
    try:
        result = ask(
            args.question,
            store,
            bm25,
            top_k=args.top_k,
            use_rerank=not args.no_rerank,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(result["answer"])

    if args.show_sources and result["sources"]:
        print("\nSources:")
        for source in result["sources"]:
            bm25_score = source["bm25_score"]
            bm25_label = f", bm25: {bm25_score}" if bm25_score is not None else ""
            print(
                f"  [{source['rank']}] {source['source']} "
                f"(semantic rank: {source['semantic_rank']}{bm25_label})"
            )
            print(f"      {source['excerpt']}")


def cmd_status(_: argparse.Namespace) -> None:
    store = VectorStore()
    bm25 = BM25Index.load()
    print(f"Vector store: {store.count()} chunks indexed")
    print(f"BM25 index: {len(bm25.records)} documents")
    print(f"Embed model: {EMBED_MODEL}")
    print(f"LLM model: {LLM_MODEL}")
    print(f"Retrieval: semantic top-{RETRIEVAL_CANDIDATES} -> BM25 rerank -> top-{TOP_K}")
    if store.list_sources():
        print("Sources:")
        for source in store.list_sources():
            print(f"  - {source}")


def cmd_reset(_: argparse.Namespace) -> None:
    store = VectorStore()
    count = store.count()
    if count == 0:
        BM25Index().reset()
        print("Vector store is already empty.")
        return

    store.reset()
    BM25Index().reset()
    print(f"Cleared vector store and BM25 index ({count} chunks removed).")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PolicyPulse — hybrid RAG for insurance policy PDF Q&A"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Load a PDF and store vectors + BM25 index")
    ingest.add_argument("document", help="Path to a .txt or .pdf file")
    ingest.add_argument("--reset", action="store_true", help="Clear indexes before ingesting")
    ingest.set_defaults(func=cmd_ingest)

    search = sub.add_parser("search", help="Search indexed documents (no LLM)")
    search.add_argument("question", help="Your search query")
    search.add_argument("--top-k", type=int, default=TOP_K, help="Final number of chunks to return")
    search.add_argument("--no-rerank", action="store_true", help="Skip BM25 reranking")
    search.set_defaults(func=cmd_search)

    ask_parser = sub.add_parser("ask", help="Ask a question about ingested policy documents")
    ask_parser.add_argument("question", help="Your question")
    ask_parser.add_argument("--top-k", type=int, default=TOP_K, help="Final number of chunks to retrieve")
    ask_parser.add_argument("--no-rerank", action="store_true", help="Skip BM25 reranking")
    ask_parser.add_argument("--show-sources", action="store_true", help="Print retrieved sources")
    ask_parser.set_defaults(func=cmd_ask)

    status = sub.add_parser("status", help="Show index and model status")
    status.set_defaults(func=cmd_status)

    reset = sub.add_parser("reset", help="Clear vector store and BM25 index")
    reset.set_defaults(func=cmd_reset)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
