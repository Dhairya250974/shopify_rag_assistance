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
MIN_TOKENS = 30   # discard chunks smaller than this (nav text, footers, etc.)

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


def split_by_sentences(text: str) -> list[str]:
    """
    Split long paragraphs on sentence boundaries while preserving common
    abbreviations that contain periods but are not sentence endings.
    """
    abbreviations = [
        "e.g.", "i.e.", "vs.", "etc.", "Dr.", "Mr.", "Mrs.", "Sr.",
        "Jr.", "Fig.", "No.",
    ]
    placeholders = {}
    protected_text = text

    for i, abbr in enumerate(abbreviations):
        placeholder = f"__ABBR_{i}__"
        placeholders[placeholder] = abbr
        protected_text = protected_text.replace(abbr, placeholder)

    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected_text)
    sentences = []

    for part in parts:
        sentence = part.strip()
        if not sentence:
            continue
        for placeholder, abbr in placeholders.items():
            sentence = sentence.replace(placeholder, abbr)
        sentences.append(sentence)

    return sentences


def extract_heading_sections(text: str) -> list[dict]:
    """
    Split article body into heading-scoped sections. Prefer H2 markdown
    headings, fall back to H1 markdown headings, then a single General section.
    """
    normalized = text.strip()
    parts = re.split(r'\n##\s+(.+)', "\n" + normalized)

    if len(parts) == 1:
        parts = re.split(r'\n#\s+(.+)', "\n" + normalized)

    if len(parts) == 1:
        return [{"heading": "General", "content": normalized}] if normalized else []

    sections = []
    preamble = parts[0].strip()
    if preamble and token_len(preamble) > MIN_TOKENS:
        sections.append({"heading": "Overview", "content": preamble})

    for i in range(1, len(parts), 2):
        heading = parts[i].strip().lstrip("#").strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if content:
            sections.append({"heading": heading, "content": content})

    return sections


def chunk_section(heading: str, content: str, chunk_size: int) -> list[str]:
    """
    Chunk a single heading section by paragraph, falling back to sentence-level
    grouping only for paragraphs that exceed the target chunk size.
    """
    if token_len(content) <= chunk_size:
        return [content]

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    chunks = []
    buffer = []

    def flush_buffer():
        if buffer:
            chunks.append("\n\n".join(buffer).strip())
            buffer.clear()

    def add_sentence_chunks(sentences: list[str]):
        sentence_buffer = []

        for sentence in sentences:
            if token_len(sentence) > chunk_size:
                if sentence_buffer:
                    chunks.append(" ".join(sentence_buffer).strip())
                    sentence_buffer.clear()
                chunks.append(sentence.strip())
                continue

            candidate = " ".join(sentence_buffer + [sentence]).strip()
            if sentence_buffer and token_len(candidate) > chunk_size:
                chunks.append(" ".join(sentence_buffer).strip())
                sentence_buffer = [sentence]
            else:
                sentence_buffer.append(sentence)

        if sentence_buffer:
            chunks.append(" ".join(sentence_buffer).strip())

    for paragraph in paragraphs:
        if token_len(paragraph) > chunk_size:
            flush_buffer()
            add_sentence_chunks(split_by_sentences(paragraph))
            continue

        candidate = "\n\n".join(buffer + [paragraph]).strip()
        if buffer and token_len(candidate) > chunk_size:
            flush_buffer()
            buffer.append(paragraph)
        else:
            buffer.append(paragraph)

    flush_buffer()
    return [chunk for chunk in chunks if chunk]


def recursive_chunk_article(body: str, chunk_size: int) -> list[dict]:
    """
    Run heading-aware recursive chunking for one article and return partial
    chunk metadata to be completed by chunk_all_articles().
    """
    sections = extract_heading_sections(body)
    all_chunks = []
    chunk_index = 0

    for section in sections:
        chunk_texts = chunk_section(section["heading"], section["content"], chunk_size)

        for chunk_text in chunk_texts:
            tok_count = token_len(chunk_text)
            if tok_count < MIN_TOKENS:
                continue

            all_chunks.append({
                "chunk_index": chunk_index,
                "heading":     section["heading"],
                "text":        chunk_text.strip(),
                "token_count": tok_count,
            })
            chunk_index += 1

    return all_chunks


# ── Main ──────────────────────────────────────────────────────────────────

def chunk_all_articles() -> list[dict]:
    """
    Process all .txt files in data/raw/ and produce a flat list of chunks.
    Each chunk: {chunk_id, title, url, section, text, token_count}
    """
    all_txt_files = list(RAW_DIR.rglob("*.txt"))
    print(f"\nFound {len(all_txt_files)} article files to process")
    print(f"Chunk size: {CHUNK_SIZE} tokens | Strategy: Recursive (Heading → Paragraph → Sentence)\n")

    all_chunks = []
    chunk_id = 0

    for filepath in tqdm(all_txt_files, desc="Chunking articles"):
        try:
            article = parse_article_file(filepath)
            body    = clean_text(article["body"])

            if len(body) < 100:
                continue   # skip nearly empty articles

            raw_chunks = recursive_chunk_article(body, CHUNK_SIZE)

            for rc in raw_chunks:
                all_chunks.append({
                    "chunk_id":    f"chunk_{chunk_id:05d}",
                    "title":       article["title"],
                    "url":         article["url"],
                    "section":     article["section"],
                    "chunk_index": rc["chunk_index"],
                    "heading":     rc["heading"],
                    "text":        rc["text"],
                    "token_count": rc["token_count"],
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
