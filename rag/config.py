from pathlib import Path

LLM_MODEL = "llama3"
EMBED_MODEL = "nomic-embed-text"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
RETRIEVAL_CANDIDATES = 20
TOP_K = 4
MAX_EXCERPT_CHARS = 500

# ChromaDB returns L2 distance (not 0–1 cosine). Typical ranges with nomic-embed-text:
# in-document ~150–350, off-topic ~550+.
STRONG_SEMANTIC_DISTANCE = 280  # auto-pass: retrieval is clearly on-topic
MAX_SEMANTIC_DISTANCE = 450  # hard refuse above this
MIN_BM25_SCORE = 0.5  # for borderline semantic matches, require some keyword overlap

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_ROOT / ".chroma"
DATA_DIR = PROJECT_ROOT / "data"
BM25_DIR = PROJECT_ROOT / ".bm25"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
COLLECTION_NAME = "policy_chunks"
