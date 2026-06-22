"""
chunker.py
──────────
Reads all .txt files from data/raw/, splits them into overlapping chunks,
attaches source metadata to each chunk, and saves to data/chunks.json.

Usage:
    python src/chunker.py
"""

import os
import re
import json
import tiktoken
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────────────────────────────────────
RAW_DIR    = Path("data/raw")
CHUNKS_OUT = Path("data/chunks.json")
CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", 400))      # tokens per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))    # overlap in tokens

# tiktoken encoder — cl100k_base works for all modern LLMs
ENCODER = tiktoken.get_encoding("cl100k_base")


# ── Helpers ───────────────────────────────────────────────────────────────

def parse_article_file(filepath: Path) -> dict:
    """
    Parse a raw article .txt file.
    Returns dict: {title, url, section, body}
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    # Split on the --- separator
    parts = raw.split("---\n\n", 1)
    header_block = parts[0]
    body = parts[1].strip() if len(parts) > 1 else ""

    # Parse header key: value lines
    meta = {}
    for line in header_block.strip().split("\n"):
        if ": " in line:
            key, val = line.split(": ", 1)
            meta[key.strip().lower()] = val.strip()

    return {
        "title":   meta.get("title", filepath.stem),
        "url":     meta.get("url", ""),
        "section": meta.get("section", "unknown"),
        "body":    body,
    }


def clean_text(text: str) -> str:
    """Light cleaning — collapse multiple blank lines, strip extra spaces."""
    text = re.sub(r'\n{3,}', '\n\n', text)       # max 2 newlines in a row
    text = re.sub(r'[ \t]+', ' ', text)           # collapse spaces/tabs
    text = re.sub(r' \n', '\n', text)             # trailing space before newline
    return text.strip()


def token_len(text: str) -> int:
    return len(ENCODER.encode(text))


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Token-aware sliding window chunker.
    Splits text into chunks of ~chunk_size tokens with overlap tokens of context.
    Tries to split on paragraph boundaries where possible.
    """
    # First split by paragraph to respect natural boundaries
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_tokens = []
    current_text_parts = []

    for para in paragraphs:
        para_tokens = ENCODER.encode(para)

        # If single paragraph already exceeds chunk size, split it by sentences
        if len(para_tokens) > chunk_size:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in sentences:
                sent_tokens = ENCODER.encode(sent)
                if len(current_tokens) + len(sent_tokens) > chunk_size:
                    if current_tokens:
                        chunks.append(" ".join(current_text_parts))
                    # Start new chunk with overlap
                    overlap_tokens = current_tokens[-overlap:] if overlap else []
                    overlap_text = ENCODER.decode(overlap_tokens)
                    current_tokens = overlap_tokens + sent_tokens
                    current_text_parts = [overlap_text, sent] if overlap_text else [sent]
                else:
                    current_tokens += sent_tokens
                    current_text_parts.append(sent)
            continue

        # Normal case: add paragraph to current chunk
        if len(current_tokens) + len(para_tokens) > chunk_size:
            if current_tokens:
                chunks.append("\n\n".join(current_text_parts))
            # Start new chunk with overlap
            overlap_tokens = current_tokens[-overlap:] if overlap else []
            overlap_text = ENCODER.decode(overlap_tokens)
            current_tokens = overlap_tokens + para_tokens
            current_text_parts = [overlap_text, para] if overlap_text.strip() else [para]
        else:
            current_tokens += para_tokens
            current_text_parts.append(para)

    # Don't forget the last chunk
    if current_text_parts:
        chunks.append("\n\n".join(current_text_parts))

    return [c.strip() for c in chunks if c.strip()]


# ── Main ──────────────────────────────────────────────────────────────────

def chunk_all_articles() -> list[dict]:
    """
    Process all .txt files in data/raw/ and produce a flat list of chunks.
    Each chunk: {chunk_id, title, url, section, text, token_count}
    """
    all_txt_files = list(RAW_DIR.rglob("*.txt"))
    print(f"\nFound {len(all_txt_files)} article files to process")
    print(f"Chunk size: {CHUNK_SIZE} tokens | Overlap: {CHUNK_OVERLAP} tokens\n")

    all_chunks = []
    chunk_id = 0

    for filepath in tqdm(all_txt_files, desc="Chunking articles"):
        try:
            article = parse_article_file(filepath)
            body    = clean_text(article["body"])

            if len(body) < 100:
                continue   # skip nearly empty articles

            raw_chunks = split_into_chunks(body, CHUNK_SIZE, CHUNK_OVERLAP)

            for i, chunk_text in enumerate(raw_chunks):
                tok_count = token_len(chunk_text)
                if tok_count < 30:
                    continue   # skip tiny fragments

                all_chunks.append({
                    "chunk_id":    f"chunk_{chunk_id:05d}",
                    "title":       article["title"],
                    "url":         article["url"],
                    "section":     article["section"],
                    "chunk_index": i,
                    "text":        chunk_text,
                    "token_count": tok_count,
                })
                chunk_id += 1

        except Exception as e:
            print(f"\n  [ERROR] {filepath.name}: {e}")
            continue

    # Save all chunks to JSON
    CHUNKS_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_OUT, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    # Summary stats
    token_counts = [c["token_count"] for c in all_chunks]
    avg_tokens   = sum(token_counts) / len(token_counts) if token_counts else 0
    sections     = {}
    for c in all_chunks:
        sections[c["section"]] = sections.get(c["section"], 0) + 1

    print(f"\n{'='*60}")
    print(f"✅ CHUNKING COMPLETE")
    print(f"   Total chunks      : {len(all_chunks)}")
    print(f"   Avg tokens/chunk  : {avg_tokens:.0f}")
    print(f"   Min tokens        : {min(token_counts) if token_counts else 0}")
    print(f"   Max tokens        : {max(token_counts) if token_counts else 0}")
    print(f"\n   Chunks per section:")
    for sec, count in sorted(sections.items()):
        print(f"     {sec:<20} {count}")
    print(f"\n   Saved to: {CHUNKS_OUT.resolve()}")
    print(f"{'='*60}")

    return all_chunks


if __name__ == "__main__":
    chunk_all_articles()
