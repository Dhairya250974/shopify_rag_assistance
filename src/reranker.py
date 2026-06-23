"""
reranker.py
-----------
Cross-encoder reranker using ms-marco-MiniLM-L-6-v2.
Takes (question, chunks) and reorders chunks by relevance score.
Runs locally via sentence-transformers - no API call, no cost.

The cross-encoder reads question + chunk TOGETHER (not separately),
giving much more accurate relevance scores than cosine similarity alone.
"""

import os
from sentence_transformers import CrossEncoder
from dotenv import load_dotenv

load_dotenv()

RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
DEFAULT_TOP_K = int(os.getenv("RERANK_TOP_K", 5))


class Reranker:
    def __init__(self):
        print(f"[Reranker] Loading model: {RERANK_MODEL}")
        self.model = CrossEncoder(RERANK_MODEL)
        print(f"[Reranker] Model ready")

    def rerank(self, question: str, chunks: list[dict], top_k: int = DEFAULT_TOP_K) -> list[dict]:
        """
        Rerank retrieved chunks by relevance to the question.

        Args:
            question: the user's question string
            chunks:   list of chunk dicts from retriever
                      each dict has at minimum: text, chunk_id, title, url, section, score
            top_k:    how many top chunks to return after reranking

        Steps:
            1. Build pairs: [(question, chunk["text"]) for each chunk]
            2. Run self.model.predict(pairs) - returns a score per pair
            3. Attach rerank_score to each chunk dict
            4. Sort chunks by rerank_score descending
            5. Re-assign rank field starting from 1
            6. Return top_k chunks only

        Returns:
            list of top_k chunk dicts, sorted by rerank_score descending
            each chunk dict now has two score fields:
              - score:        original cosine similarity score from retriever
              - rerank_score: cross-encoder score (higher = more relevant)

        Important:
            - top_k must not exceed len(chunks). If top_k > len(chunks),
              return all chunks sorted by rerank_score.
            - Do not modify any other field in the chunk dicts.
            - rerank_score should be rounded to 4 decimal places.
        """

        if not chunks:
            return []

        pairs = [(question, chunk["text"]) for chunk in chunks]
        scores = self.model.predict(pairs)

        for chunk, score in zip(chunks, scores):
            chunk["rerank_score"] = round(float(score), 4)

        reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)

        top = reranked[:top_k]
        for i, chunk in enumerate(top):
            chunk["rank"] = i + 1

        return top


if __name__ == "__main__":
    # Quick smoke test
    from retriever import Retriever

    retriever = Retriever()
    reranker = Reranker()

    query = "How do I set up free shipping on Shopify?"
    print(f"\nQuery: {query}")

    chunks = retriever.retrieve(query, top_k=10)
    print(f"\nBefore reranking (top 5 of 10 by cosine score):")
    for c in chunks[:5]:
        print(f"  [{c['rank']}] score={c['score']:.4f} | {c['title'][:50]} | {c.get('heading','')[:30]}")

    reranked = reranker.rerank(query, chunks, top_k=5)
    print(f"\nAfter reranking (top 5 by cross-encoder score):")
    for c in reranked:
        print(f"  [{c['rank']}] rerank={c['rerank_score']:.4f} | cosine={c['score']:.4f} | {c['title'][:50]} | {c.get('heading','')[:30]}")
