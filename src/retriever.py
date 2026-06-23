"""
retriever.py  (v4 — pure numpy cosine search)
───────────────────────────────────────────────
Loads embeddings.npy and does brute-force cosine similarity search.
For 147 chunks this is ~1ms per query — faster than any vector DB overhead.
Zero C++ dependencies.
"""

import os
import json
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

INDEX_DIR   = Path("data/np_index")
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")
TOP_K       = int(os.getenv("TOP_K", 5))
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class Retriever:
    def __init__(self):
        from sentence_transformers import SentenceTransformer

        print(f"[Retriever] Loading embedding model: {EMBED_MODEL}")
        self.model = SentenceTransformer(EMBED_MODEL)

        print(f"[Retriever] Loading numpy index from: {INDEX_DIR}")
        self.embeddings = np.load(str(INDEX_DIR / "embeddings.npy"))

        with open(INDEX_DIR / "metadata.json", "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        print(f"[Retriever] ✓ Ready — {len(self.metadata)} chunks loaded")

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        # Embed and normalize query
        query_emb = self.model.encode(
            [BGE_QUERY_PREFIX + query], normalize_embeddings=True
        ).astype("float32")

        # Cosine similarity = dot product on normalized vectors
        scores = (self.embeddings @ query_emb.T).flatten()

        # Get top-k indices sorted by score descending
        top_indices = np.argsort(scores)[::-1][:top_k]

        hits = []
        for rank, idx in enumerate(top_indices):
            meta = self.metadata[idx]
            hits.append({
                "rank":     rank + 1,
                "chunk_id": meta["chunk_id"],
                "text":     meta["text"],
                "title":    meta["title"],
                "url":      meta["url"],
                "section":  meta["section"],
                "heading":  meta.get("heading", ""),
                "score":    round(float(scores[idx]), 4),
            })

        return hits


if __name__ == "__main__":
    retriever = Retriever()

    test_queries = [
        "How do I set up shipping rates on Shopify?",
        "How can I process a refund for a customer order?",
        "What payment gateways does Shopify support?",
        "How do I add product variants like size and color?",
        "How to set up abandoned cart email recovery?",
    ]

    for query in test_queries:
        print(f"\n{'─'*60}")
        print(f"Query: {query}")
        hits = retriever.retrieve(query, top_k=3)
        for h in hits:
            print(f"  [{h['rank']}] score={h['score']:.4f} | {h['title'][:60]}")
            print(f"       section={h['section']}")
            print(f"       preview: {h['text'][:120]}...")
