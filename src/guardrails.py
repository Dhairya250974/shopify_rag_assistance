"""
guardrails.py
-------------
Two-layer guardrail system for the Shopify RAG pipeline.

Layer 1 - Groq LLM topic check (fast YES/NO before any retrieval):
  Sends question to Groq with max_tokens=5.
  Keyword fast-pass skips the Groq call for obvious Shopify questions.
  If off-topic, reject immediately with no retrieval, embedding, or LLM cost.

Layer 2 - Retrieval score threshold check:
  After vector search, checks top chunk cosine score.
  If score < SCORE_THRESHOLD, no relevant docs found, reject.
  Fires before reranking and generation.

Fail-open design: if Groq guardrail call fails for any reason, allow through.
A broken guardrail must never break the main pipeline.
"""

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY        = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY_1")
GROQ_API_URL        = "https://api.groq.com/openai/v1/chat/completions"
GUARDRAIL_MODEL     = os.getenv("GUARDRAIL_MODEL", "llama-3.3-70b-versatile")
SCORE_THRESHOLD     = float(os.getenv("GUARDRAIL_SCORE_THRESHOLD", "0.30"))

REJECTION_MESSAGE = (
    "I can only answer questions about Shopify. "
    "Please ask me about store setup, products, orders, payments, "
    "shipping, marketing, themes, customers, or analytics."
)

LOW_SCORE_MESSAGE = (
    "I couldn't find relevant Shopify documentation for your question. "
    "Try rephrasing, or ask about products, orders, shipping, "
    "payments, marketing, or store settings."
)

GUARDRAIL_SYSTEM_PROMPT = """You are a query guardrail for a Shopify help assistant.

Decide if the user question is related to Shopify or not.

Shopify-related topics:
- Store setup and configuration
- Products, variants, inventory, collections
- Orders, fulfillment, refunds, cancellations
- Payments, checkout, taxes, transaction fees
- Shipping, delivery, rates, profiles
- Marketing, SEO, discounts, email marketing
- Themes, pages, blogs, navigation, domains
- Customers, accounts, segmentation
- Analytics, reports
- Apps and integrations
- Shopify plans and pricing

Answer ONLY with YES or NO. Nothing else.
YES = question is about Shopify or running a Shopify store
NO  = question is off-topic or unrelated to Shopify

Examples:
"How do I set up free shipping?" -> YES
"What is the capital of France?" -> NO
"How do I add product variants?" -> YES
"Tell me a joke" -> NO
"How do I recover abandoned carts?" -> YES
"What is the weather in London?" -> NO"""

# Keywords that guarantee a question is Shopify-related
# If any keyword matches, skip the Groq call entirely (fast-pass)
SHOPIFY_KEYWORDS = [
    "shopify", "store", "product", "order", "shipping", "payment",
    "customer", "inventory", "checkout", "refund", "discount",
    "theme", "domain", "marketing", "analytics", "variant", "cart",
    "collection", "fulfillment", "invoice", "tax", "seo", "blog",
    "storefront", "admin", "plan", "subscription", "app", "plugin",
]


class GuardrailResult:
    """
    Result object returned by both guardrail layers.

    Fields:
      passed  (bool) - True if question should proceed through pipeline
      message (str)  - rejection message if passed=False, empty if passed=True
      layer   (str)  - which layer caught it: "topic", "score", or "none"
    """
    def __init__(self, passed: bool, message: str = "", layer: str = "none"):
        self.passed  = passed
        self.message = message
        self.layer   = layer


def check_topic(question: str) -> GuardrailResult:
    """
    Layer 1 - Groq LLM topic guardrail with keyword fast-pass.

    Step 1: Check if question contains any SHOPIFY_KEYWORDS.
            If yes, return GuardrailResult(passed=True) immediately.
            No Groq call needed, question is clearly Shopify-related.

    Step 2: If no keywords matched, call Groq with YES/NO prompt.
            Parse response:
              starts with "YES" -> passed=True
              starts with "NO"  -> passed=False, message=REJECTION_MESSAGE, layer="topic"

    Step 3: If Groq call fails for ANY reason (timeout, error, exception):
            Log warning and return GuardrailResult(passed=True).
            FAIL OPEN - never block on guardrail failure.
    """

    # Step 1 - keyword fast-pass
    question_lower = question.lower()
    if any(kw in question_lower for kw in SHOPIFY_KEYWORDS):
        return GuardrailResult(passed=True)

    # Step 2 - Groq LLM check for ambiguous questions
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GUARDRAIL_MODEL,
            messages=[
                {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
                {"role": "user",   "content": question},
            ],
            max_tokens=5,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip().upper()

        if answer.startswith("NO"):
            return GuardrailResult(
                passed=False,
                message=REJECTION_MESSAGE,
                layer="topic",
            )
        return GuardrailResult(passed=True)

    except Exception as e:
        # Step 3 - fail open on any error
        print(f"[Guardrail] Layer 1 check failed: {e} - allowing through")
        return GuardrailResult(passed=True)


def check_score(top_score: float) -> GuardrailResult:
    """
    Layer 2 - Retrieval confidence threshold check.

    Args:
        top_score: cosine similarity score of the top retrieved chunk

    Logic:
        if top_score < SCORE_THRESHOLD:
            return GuardrailResult(passed=False, message=LOW_SCORE_MESSAGE, layer="score")
        else:
            return GuardrailResult(passed=True)
    """
    if top_score < SCORE_THRESHOLD:
        return GuardrailResult(
            passed=False,
            message=LOW_SCORE_MESSAGE,
            layer="score",
        )
    return GuardrailResult(passed=True)


if __name__ == "__main__":
    """
    Smoke test - python src/guardrails.py
    Tests Layer 1 with on-topic and off-topic questions.
    Tests Layer 2 with various score values.
    """
    print("\n" + "="*60)
    print("GUARDRAIL LAYER 1 - Topic Check")
    print("="*60)

    test_cases = [
        ("How do I set up free shipping on Shopify?",          True),
        ("What is the capital of France?",                     False),
        ("How do I add product variants like size and color?", True),
        ("Tell me a joke",                                     False),
        ("How do I connect a custom domain to my store?",      True),
        ("What is the stock price of Shopify?",                False),
        ("How do I process a refund for a customer?",          True),
        ("Write me a poem about summer",                       False),
    ]

    for question, expected_pass in test_cases:
        result = check_topic(question)
        status = "PASS" if result.passed else f"BLOCKED (layer={result.layer})"
        match  = "OK" if result.passed == expected_pass else "UNEXPECTED"
        print(f"\n  {match} Q: {question[:55]}")
        print(f"       Result: {status}")

    print("\n" + "="*60)
    print("GUARDRAIL LAYER 2 - Score Threshold Check")
    print("="*60)

    score_tests = [
        (0.45, True),
        (0.31, True),
        (0.30, True),
        (0.29, False),
        (0.10, False),
    ]

    for score, expected_pass in score_tests:
        result = check_score(score)
        status = "PASS" if result.passed else f"BLOCKED (layer={result.layer})"
        match  = "OK" if result.passed == expected_pass else "UNEXPECTED"
        print(f"\n  {match} Score: {score} -> {status}")

    print("\nGuardrail smoke test complete.")
