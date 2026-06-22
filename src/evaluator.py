"""
evaluator.py
────────────
Runs the golden Q&A set through the retriever and computes:
  - Hit Rate@1, Hit Rate@3, Hit Rate@5
  - MRR (Mean Reciprocal Rank)
  - Per-section breakdown

A "hit" = the retrieved chunk's section matches the expected section
OR the chunk text contains at least 2 of the expected keywords.

Usage:
    python src/evaluator.py
"""

import json
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from retriever import Retriever

load_dotenv()

GOLDEN_SET_PATH = Path("golden_set/questions.json")
RESULTS_DIR     = Path("data/eval_results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

K_VALUES = [1, 3, 5]


def is_hit(chunk: dict, expected_section: str, expected_keywords: list[str]) -> bool:
    """
    A chunk is a 'hit' if:
      1. Its section matches the expected section, OR
      2. Its text contains at least 2 of the expected keywords (case-insensitive)
    This dual check avoids penalizing cross-section answers that are still correct.
    """
    # Section match
    if chunk.get("section", "").lower() == expected_section.lower():
        return True

    # Keyword match
    text_lower = chunk.get("text", "").lower()
    title_lower = chunk.get("title", "").lower()
    combined = text_lower + " " + title_lower
    matched = sum(1 for kw in expected_keywords if kw.lower() in combined)
    return matched >= 2


def reciprocal_rank(chunks: list[dict], expected_section: str, expected_keywords: list[str]) -> float:
    """Return 1/rank of the first hit, or 0.0 if no hit found."""
    for i, chunk in enumerate(chunks):
        if is_hit(chunk, expected_section, expected_keywords):
            return 1.0 / (i + 1)
    return 0.0


def run_evaluation(top_k: int = 5) -> dict:
    """
    Run full evaluation over golden set.
    Returns summary dict + per-question results.
    """
    with open(GOLDEN_SET_PATH, "r") as f:
        questions = json.load(f)

    retriever = Retriever()

    per_question = []
    hit_counts   = {k: 0 for k in K_VALUES}
    rr_scores    = []

    print(f"\nRunning evaluation on {len(questions)} questions (top_k={top_k})")
    print("─" * 65)

    for q in questions:
        qid      = q["id"]
        question = q["question"]
        exp_sec  = q["expected_section"]
        exp_kws  = q["expected_keywords"]

        chunks = retriever.retrieve(question, top_k=top_k)

        # Compute hits at each K
        hits_at = {}
        for k in K_VALUES:
            top_chunks = chunks[:k]
            hit = any(is_hit(c, exp_sec, exp_kws) for c in top_chunks)
            hits_at[k] = int(hit)
            if hit:
                hit_counts[k] += 1

        # Reciprocal rank
        rr = reciprocal_rank(chunks, exp_sec, exp_kws)
        rr_scores.append(rr)

        # Top result info
        top = chunks[0] if chunks else {}

        per_question.append({
            "id":              qid,
            "question":        question,
            "expected_section": exp_sec,
            "top_section":     top.get("section", ""),
            "top_title":       top.get("title", "")[:60],
            "top_score":       top.get("score", 0),
            "hit@1":           hits_at[1],
            "hit@3":           hits_at[3],
            "hit@5":           hits_at[5],
            "rr":              round(rr, 4),
        })

        status = "✓" if hits_at[5] else "✗"
        print(f"  [{status}] {qid} | RR={rr:.2f} | {question[:55]}")

        time.sleep(0.2)   # small pause to avoid hammering chroma

    # ── Aggregate metrics ──
    n = len(questions)
    summary = {
        "total_questions": n,
        "hit_rate@1":  round(hit_counts[1] / n * 100, 2),
        "hit_rate@3":  round(hit_counts[3] / n * 100, 2),
        "hit_rate@5":  round(hit_counts[5] / n * 100, 2),
        "mrr":         round(sum(rr_scores) / n, 4),
    }

    # ── Per-section breakdown ──
    df = pd.DataFrame(per_question)
    section_breakdown = (
        df.groupby("expected_section")[["hit@1","hit@3","hit@5","rr"]]
        .mean()
        .round(3)
        .to_dict(orient="index")
    )

    # ── Save results ──
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_path = RESULTS_DIR / f"eval_{timestamp}.json"
    full_results = {
        "summary":           summary,
        "section_breakdown": section_breakdown,
        "per_question":      per_question,
    }
    with open(results_path, "w") as f:
        json.dump(full_results, f, indent=2)

    # Save CSV for easy viewing
    csv_path = RESULTS_DIR / f"eval_{timestamp}.csv"
    df.to_csv(csv_path, index=False)

    # ── Print summary ──
    print(f"\n{'='*65}")
    print(f"✅ EVALUATION RESULTS")
    print(f"{'='*65}")
    print(f"  Total questions  : {n}")
    print(f"  Hit Rate@1       : {summary['hit_rate@1']}%")
    print(f"  Hit Rate@3       : {summary['hit_rate@3']}%")
    print(f"  Hit Rate@5       : {summary['hit_rate@5']}%")
    print(f"  MRR              : {summary['mrr']}")
    print(f"\n  Section Breakdown:")
    for sec, metrics in section_breakdown.items():
        print(f"    {sec:<20} HR@5={metrics['hit@5']:.2f}  MRR={metrics['rr']:.3f}")
    print(f"\n  Results saved to:")
    print(f"    {results_path}")
    print(f"    {csv_path}")
    print(f"{'='*65}")

    return full_results


if __name__ == "__main__":
    run_evaluation(top_k=5)
