# Shopify RAG Assistant

An AI-powered assistant for Shopify store operators. Ask natural-language questions and get grounded answers from indexed Shopify Help Center documentation.

## Overview

This project implements a local Retrieval-Augmented Generation pipeline over selected public Shopify documentation. It includes:

| Component | Current Implementation |
|---|---|
| Data source | Shopify Help Center pages |
| Scraping | Selenium headless Chrome |
| Chunking | Token-aware sliding window with `tiktoken` |
| Embeddings | `all-MiniLM-L6-v2` via `sentence-transformers` |
| Vector storage | Local NumPy index in `data/np_index/` |
| Retrieval | Brute-force cosine similarity over normalized embeddings |
| LLM | Llama 3.3 70B via Groq API |
| API | FastAPI in `api/main.py` |
| Legacy UI | Flask app in `ui/app.py` |
| New UI | React + TypeScript + Vite + Tailwind CSS in `frontend/` |
| Evaluation | Custom retrieval eval: Hit Rate@k + MRR |

The backend request and response contracts are unchanged. The new React frontend calls the existing `POST /query` endpoint.

## Project Structure

```text
shopify-rag-assistant/
├── api/
│   └── main.py                  # FastAPI REST API
├── data/
│   ├── raw/                     # scraped Shopify help articles
│   ├── chunks.json              # processed text chunks
│   ├── np_index/                # local NumPy vector index + metadata
│   └── eval_results/            # evaluation JSON/CSV outputs
├── frontend/                    # modern React frontend
│   ├── src/
│   │   ├── components/          # chat, sidebar, source cards, states
│   │   ├── hooks/               # chat state hook
│   │   ├── pages/               # Home page
│   │   ├── services/            # API integration
│   │   └── types/               # TypeScript API types
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── golden_set/
│   └── questions.json           # 25 retrieval evaluation questions
├── src/
│   ├── scraper.py               # scrape Shopify docs with Selenium
│   ├── chunker.py               # clean + chunk raw articles
│   ├── embedder.py              # embed chunks into local NumPy index
│   ├── retriever.py             # cosine similarity retrieval
│   ├── generator.py             # Groq LLM answer generation
│   ├── pipeline.py              # end-to-end RAG pipeline
│   └── evaluator.py             # Hit Rate + MRR evaluation
├── ui/
│   ├── app.py                   # legacy Flask UI/backend endpoint
│   └── templates/index.html     # legacy HTML template
├── requirements.txt
└── README.md
```

## Backend Setup

Create and activate a Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```bash
cp .env.example .env
```

Add at least one Groq key:

```env
GROQ_API_KEY_1=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
EMBED_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=400
CHUNK_OVERLAP=50
TOP_K=5
```

Note: the current scraper uses Selenium/Chrome. Make sure Chrome is installed locally before running `src/scraper.py`.

## RAG Pipeline

Run these commands from the repository root.

### 1. Scrape Shopify Help Center

```bash
python src/scraper.py
```

Writes article text files to `data/raw/` and a manifest to `data/raw/manifest.json`.

### 2. Chunk Articles

```bash
python src/chunker.py
```

Reads `data/raw/**/*.txt` and writes token-aware chunks to `data/chunks.json`.

### 3. Generate Embeddings

```bash
python src/embedder.py
```

Embeds chunks with `all-MiniLM-L6-v2` and writes:

```text
data/np_index/embeddings.npy
data/np_index/metadata.json
data/np_index/config.json
```

### 4. Test Retrieval

```bash
python src/retriever.py
```

Runs sample queries and prints top retrieved chunks.

### 5. Test End-to-End RAG

```bash
python src/pipeline.py
```

Runs sample questions through retrieval and Groq answer generation.

### 6. Run Evaluation

```bash
python src/evaluator.py
```

Evaluates retrieval over `golden_set/questions.json` and saves JSON/CSV outputs under `data/eval_results/`.

Latest checked-in eval artifacts show:

| Metric | Value |
|---|---:|
| Total questions | 25 |
| Hit Rate@1 | 88.0% |
| Hit Rate@3 | 96.0% |
| Hit Rate@5 | 96.0% |
| MRR | 0.92 |

## Running the Backend

### Option A: Legacy Flask UI + `/query`

The new React frontend is configured to proxy `/query` to this Flask app during local development.

```bash
python ui/app.py
```

Flask runs on:

```text
http://localhost:5000
```

Endpoint:

```http
POST /query
```

Request:

```json
{
  "question": "How do I set up free shipping?"
}
```

Response:

```json
{
  "answer": "...",
  "sources": [
    {
      "title": "...",
      "url": "..."
    }
  ],
  "latency_ms": 423,
  "model": "llama-3.3-70b-versatile",
  "chunks_used": 5
}
```

### Option B: FastAPI API

```bash
uvicorn api.main:app --reload --port 8000
```

Open:

```text
http://localhost:8000/docs
```

Endpoints:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/query` | Ask a Shopify question |
| `GET` | `/stats` | Intended stats endpoint |

Note: `/stats` currently references an older Chroma-style `collection` attribute and should be updated before relying on it. The active retriever uses the local NumPy index.

## Running the New React Frontend

The redesigned frontend lives in `frontend/` and does not modify backend logic or API schemas.

Install dependencies:

```bash
cd frontend
npm install
```

Start the frontend:

```bash
npm run dev
```

Open the Vite URL, usually:

```text
http://localhost:5173
```

For local chat requests, also run the Flask backend in another terminal:

```bash
python ui/app.py
```

The Vite dev server proxies frontend calls from `/query` to:

```text
http://localhost:5000/query
```

Build the production frontend:

```bash
cd frontend
npm run build
```

The production build is emitted to `frontend/dist/`.

## Frontend Features

The new React UI includes:

- Modern two-section layout with responsive sidebar
- Welcome hero and suggested question cards
- ChatGPT-style conversation UX
- Markdown assistant answers with code block support
- Source cards instead of plain links
- Copy answer button
- Loading skeleton and retrieval animation
- Polished error states
- Recent questions stored in `localStorage`
- Dark mode toggle persisted in `localStorage`
- Mobile/tablet sidebar collapse

## Evaluation Methodology

`src/evaluator.py` evaluates retrieval, not generated answer quality.

A retrieved chunk is counted as a hit when:

- its `section` matches the expected section, or
- its title/text contains at least two expected keywords.

Metrics:

| Metric | Description |
|---|---|
| Hit Rate@1 | Percentage of questions with a hit in the top result |
| Hit Rate@3 | Percentage of questions with a hit in top 3 |
| Hit Rate@5 | Percentage of questions with a hit in top 5 |
| MRR | Mean reciprocal rank of the first hit |

## Important Implementation Notes

- The current vector store is `data/np_index/`, not ChromaDB.
- Retrieval is exact brute-force NumPy cosine similarity, which is appropriate for the current 147-chunk dataset.
- The README previously referenced Gradio/ChromaDB/BeautifulSoup; those are not the active implementation.
- The React frontend preserves the existing `POST /query` request and response schema.
- The legacy Flask HTML UI remains in `ui/templates/index.html` for compatibility.

## Production Scaling Path

Recommended next steps:

1. Fix FastAPI `/stats` for the NumPy retriever.
2. Add missing backend dependency alignment for Selenium/Flask if needed.
3. Add authentication and rate limiting.
4. Add structured logs, request IDs, latency metrics, and token/cost tracking.
5. Add retrieval confidence thresholds and answer-groundedness evaluation.
6. Add hybrid retrieval and reranking.
7. Move from local NumPy search to FAISS/HNSW, pgvector, Pinecone, or Weaviate for larger corpora.
8. Add deployment packaging for the React frontend and backend services.
