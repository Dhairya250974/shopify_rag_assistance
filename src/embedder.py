"""
embedder.py  (v4 — pure numpy, no C++ needed)
───────────────────────────────────────────────
Embeds chunks with sentence-transformers and saves embeddings
as a numpy .npy file + metadata JSON. Zero external vector DB needed.
For 147 chunks, numpy cosine search is instant (~1ms per query).

Usage:
    python src/embedder.py
"""

import os
import json
import numpy as np
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

CHUNKS_FILE = Path("data/chunks.json")
INDEX_DIR   = Path("data/np_index")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
BATCH_SIZE  = 64


def load_chunks() -> list[dict]:
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_vector_store(chunks: list[dict]):
    from sentence_transformers import SentenceTransformer

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nLoading embedding model: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)
    dim   = model.get_sentence_embedding_dimension()
    print(f"  ✓ Model loaded  |  Embedding dim: {dim}")

    print(f"\nEmbedding {len(chunks)} chunks in batches of {BATCH_SIZE}...")
    texts = [c["text"] for c in chunks]
    all_embeddings = []

    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Embedding"):
        batch = texts[i : i + BATCH_SIZE]
        embs  = model.encode(
            batch,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        all_embeddings.append(embs)

    embeddings = np.vstack(all_embeddings).astype("float32")

    # Save embeddings as numpy array
    np.save(str(INDEX_DIR / "embeddings.npy"), embeddings)

    # Save metadata
    metadata = [
        {
            "chunk_id":    c["chunk_id"],
            "title":       c["title"],
            "url":         c["url"],
            "section":     c["section"],
            "chunk_index": c["chunk_index"],
            "token_count": c["token_count"],
            "text":        c["text"],
        }
        for c in chunks
    ]
    with open(INDEX_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    # Save config
    with open(INDEX_DIR / "config.json", "w") as f:
        json.dump({"dim": dim, "num_chunks": len(chunks), "model": EMBED_MODEL}, f)

    print(f"\n{'='*60}")
    print(f"✅ EMBEDDING COMPLETE")
    print(f"   Chunks embedded  : {len(chunks)}")
    print(f"   Embeddings shape : {embeddings.shape}")
    print(f"   Saved to         : {INDEX_DIR.resolve()}")
    print(f"   Embed model      : {EMBED_MODEL}")
    print(f"{'='*60}")


if __name__ == "__main__":
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE}")
    build_vector_store(chunks)