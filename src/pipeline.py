"""
pipeline.py
───────────
Main RAG pipeline. Combines Retriever + Generator into a single
clean interface used by the API and UI.

Usage:
    python src/pipeline.py
"""

import os
import time
from dotenv import load_dotenv
from retriever import Retriever
from reranker import Reranker
from generator import Generator
from guardrails import check_topic, check_score, GuardrailResult

load_dotenv()

TOP_K = int(os.getenv("TOP_K", 5))


class RAGPipeline:
    """
    End-to-end RAG pipeline:
        query → retrieve top-k chunks → generate grounded answer
    """

    def __init__(self):
        print("\n[RAGPipeline] Initialising...")
        self.retriever = Retriever()
        self.reranker = Reranker()
        self.generator = Generator()
        print("[RAGPipeline] ✓ Ready\n")

    def _guardrail_response(self, question: str, result: GuardrailResult, t0: float) -> dict:
        """Build a consistent response dict when a guardrail blocks a query."""
        return {
            "question":            question,
            "answer":              result.message,
            "sources":             [],
            "chunks":              [],
            "latency_ms":          round((time.time() - t0) * 1000, 1),
            "model":               "guardrail",
            "chunks_used":         0,
            "guardrail_triggered": True,
            "guardrail_layer":     result.layer,
        }

    def query(self, question: str, top_k: int = TOP_K) -> dict:
        """
        Run the full RAG pipeline for a single question.

        Returns:
            {
                question:     str,
                answer:       str,
                sources:      list[{title, url}],
                chunks:       list[retrieved chunk dicts],
                latency_ms:   float,
                model:        str,
                chunks_used:  int,
            }
        """
        t0 = time.time()

        # Layer 1 Guardrail — topic check before any retrieval
        topic_check = check_topic(question)
        if not topic_check.passed:
            return self._guardrail_response(question, topic_check, t0)

        # Step 1: Retrieve relevant chunks
        chunks = self.retriever.retrieve(question, top_k=10)

        # Guard: no chunks returned — corpus has no relevant docs
        if not chunks:
            return {
                "question":   question,
                "answer":     "I couldn't find any relevant Shopify documentation "
                              "for your question. Try rephrasing or ask about "
                              "products, orders, shipping, payments, or store settings.",
                "sources":    [],
                "chunks":     [],
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "model":      "none",
                "chunks_used": 0,
                "guardrail_triggered": False,
                "guardrail_layer":     "none",
            }

        # Layer 2 Guardrail — score threshold after retrieval, before reranking
        score_check = check_score(chunks[0]["score"])
        if not score_check.passed:
            return self._guardrail_response(question, score_check, t0)

        # Step 2: Rerank chunks by question relevance
        chunks = self.reranker.rerank(question, chunks, top_k=top_k)

        # Step 3: Generate answer from chunks
        gen_result = self.generator.generate(question, chunks)

        latency_ms = round((time.time() - t0) * 1000, 1)

        # Attach heading to each chunk for UI display
        for chunk in chunks:
            chunk.setdefault("heading", "")

        return {
            "question":   question,
            "answer":     gen_result["answer"],
            "sources":    gen_result["sources"],
            "chunks":     chunks,
            "latency_ms": latency_ms,
            "model":      gen_result["model"],
            "chunks_used": gen_result["chunks_used"],
            "guardrail_triggered": False,
            "guardrail_layer":     "none",
        }

    def format_response(self, result: dict) -> str:
        """Human-readable formatted response for CLI/testing."""
        lines = [
            f"\n{'='*65}",
            f"Q: {result['question']}",
            f"{'='*65}",
            f"\n{result['answer']}",
            f"\n{'─'*65}",
            f"Sources:",
        ]
        for s in result["sources"]:
            lines.append(f"  • {s['title']}")
            lines.append(f"    {s['url']}")
        lines.append(f"\nLatency: {result['latency_ms']}ms | Model: {result['model']}")
        lines.append(f"Chunks used: {result['chunks_used']}")
        lines.append("="*65)
        return "\n".join(lines)


# ── Interactive CLI test ──────────────────────────────────────────────────
if __name__ == "__main__":
    pipeline = RAGPipeline()

    demo_questions = [
        "How do I set up free shipping for orders above $50 on Shopify?",
        "What is the difference between Shopify Basic and Shopify Advanced plan?",
        "How do I add product variants like size and color?",
        "How can I recover abandoned carts on my Shopify store?",
        "How do I connect a custom domain to my Shopify store?",
    ]

    print("\n" + "="*65)
    print("SHOPIFY RAG ASSISTANT — Demo Run")
    print("="*65)

    for q in demo_questions:
        result = pipeline.query(q)
        print(pipeline.format_response(result))
        time.sleep(1)   # small pause between queries

    print("\n✅ Demo complete.")
