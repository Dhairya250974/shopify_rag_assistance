"""
generator.py
────────────
Takes a query + retrieved chunks, calls Groq LLM to generate
a grounded, cited answer. Implements multi-key rotation with
exponential backoff for rate limit handling.

Used by pipeline.py and the API.
"""

import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

# ── Groq multi-key setup ──────────────────────────────────────────────────
def _load_groq_keys() -> list[str]:
    keys = []
    for i in range(1, 10):
        k = os.getenv(f"GROQ_API_KEY_{i}")
        if k and k != f"your_groq_key_{i}_here":
            keys.append(k)
    # Also accept single GROQ_API_KEY
    single = os.getenv("GROQ_API_KEY")
    if single and single not in keys:
        keys.append(single)
    return keys

GROQ_KEYS           = _load_groq_keys()
GROQ_MODEL          = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MODEL_FALLBACK = os.getenv("GROQ_MODEL_FALLBACK", "llama-3.1-8b-instant")

# ── System prompt ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a helpful Shopify store assistant. You answer questions 
about running a Shopify store using ONLY the provided context from Shopify's official 
help documentation.

Rules:
- Answer clearly and concisely based on the context provided.
- If the context doesn't contain enough information to answer, say so honestly.
- Always cite which article(s) your answer comes from using [Source: Title] format.
- Format your answer in a readable way — use bullet points for steps where helpful.
- Do NOT make up information that isn't in the context.
"""

def _make_context_block(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the prompt."""
    parts = []
    for i, chunk in enumerate(chunks):
        parts.append(
            f"[Context {i+1}]\n"
            f"Source: {chunk['title']}\n"
            f"Section: {chunk.get('heading', '')}\n"
            f"URL: {chunk['url']}\n"
            f"---\n"
            f"{chunk['text']}\n"
        )
    return "\n\n".join(parts)


class Generator:
    """
    LLM answer generator with Groq multi-key rotation + exponential backoff.
    """

    def __init__(self):
        if not GROQ_KEYS:
            raise ValueError(
                "No Groq API keys found. "
                "Set GROQ_API_KEY_1 (or GROQ_API_KEY) in your .env file."
            )
        print(f"[Generator] Loaded {len(GROQ_KEYS)} Groq API key(s)")
        print(f"[Generator] Model: {GROQ_MODEL}")
        self._key_index = 0

    def _next_key(self) -> str:
        """Round-robin key rotation."""
        key = GROQ_KEYS[self._key_index % len(GROQ_KEYS)]
        self._key_index += 1
        return key

    def _call_groq(self, messages: list[dict], retries: int = 3) -> str:
        """
        Call Groq API with retry + exponential backoff on rate limit (429).
        Rotates to next key on each retry.
        """
        from groq import Groq, RateLimitError

        last_error = None
        for attempt in range(retries):
            key = self._next_key()
            try:
                client   = Groq(api_key=key)
                response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    temperature=0.2,    # low temp → factual, grounded answers
                    max_tokens=1024,
                )
                return response.choices[0].message.content

            except RateLimitError as e:
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"  [RateLimit] Key rotated. Waiting {wait:.1f}s... (attempt {attempt+1}/{retries})")
                time.sleep(wait)
                last_error = e

            except Exception as e:
                print(f"  [GeneratorError] {e}")
                last_error = e
                time.sleep(1)

        # Primary model exhausted — try fallback model once
        if GROQ_MODEL_FALLBACK and GROQ_MODEL_FALLBACK != GROQ_MODEL:
            print(f"  [Generator] Primary model failed. Trying fallback: {GROQ_MODEL_FALLBACK}")
            try:
                from groq import Groq
                key      = self._next_key()
                client   = Groq(api_key=key)
                response = client.chat.completions.create(
                    model=GROQ_MODEL_FALLBACK,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=1024,
                )
                return response.choices[0].message.content
            except Exception as fallback_error:
                print(f"  [Generator] Fallback also failed: {fallback_error}")

        raise RuntimeError(f"Groq call failed after {retries} attempts: {last_error}")

    def generate(self, query: str, chunks: list[dict]) -> dict:
        """
        Generate a grounded answer for the query using retrieved chunks.

        Returns:
            {
                answer: str,
                sources: list of {title, url},
                model: str,
                chunks_used: int,
            }
        """
        if not chunks:
            return {
                "answer":      "I couldn't find relevant information in the Shopify documentation for your question.",
                "sources":     [],
                "model":       GROQ_MODEL,
                "chunks_used": 0,
            }

        context_block = _make_context_block(chunks)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Context from Shopify Help Center:\n\n"
                    f"{context_block}\n\n"
                    f"Question: {query}\n\n"
                    f"Answer:"
                ),
            },
        ]

        answer = self._call_groq(messages)

        # Deduplicate sources
        seen = set()
        sources = []
        for c in chunks:
            key = c["url"]
            if key not in seen:
                seen.add(key)
                sources.append({
                    "title":        c["title"],
                    "url":          c["url"],
                    "heading":      c.get("heading", ""),
                    "section":      c.get("section", ""),
                    "score":        round(float(c.get("score", 0)), 4),
                    "rerank_score": round(float(c.get("rerank_score", 0)), 4),
                })

        return {
            "answer":      answer,
            "sources":     sources,
            "model":       GROQ_MODEL,
            "chunks_used": len(chunks),
        }


# ── Quick test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Minimal test without retriever — just checks LLM connection
    gen = Generator()

    dummy_chunks = [
        {
            "title": "Setting up shipping rates",
            "url":   "https://help.shopify.com/en/manual/shipping",
            "text":  (
                "You can set up shipping rates in your Shopify admin by going to "
                "Settings > Shipping and delivery. From there you can create "
                "shipping profiles and add rates based on price, weight, or "
                "offer free shipping above a certain order value."
            ),
        }
    ]

    result = gen.generate(
        query="How do I set up free shipping on Shopify?",
        chunks=dummy_chunks,
    )

    print("\n" + "="*60)
    print("ANSWER:")
    print(result["answer"])
    print("\nSOURCES:")
    for s in result["sources"]:
        print(f"  - {s['title']}: {s['url']}")
    print("="*60)
