# Shopify RAG Assistant

An AI-powered assistant for Shopify store operators. It answers natural-language questions using scraped Shopify Help Center documentation, local embeddings, cosine retrieval, cross-encoder reranking, guardrails, and a Groq-hosted LLM.

The project has two main parts:

- A Python RAG backend in `src/`, exposed through Flask in `ui/app.py` and FastAPI in `api/main.py`.
- A separate React/Vite frontend in `frontend-js/` that talks to the Flask backend during local development.

## Current Architecture

```text
User question
  -> guardrail topic check
  -> NumPy cosine retrieval, top 10
  -> empty-result and score guardrails
  -> cross-encoder reranking, top 5
  -> Groq answer generation
  -> JSON response with answer, sources, latency, model, and chunks used
```

| Component | Current Implementation |
|---|---|
| Data source | Public Shopify Help Center pages |
| Scraping | Selenium headless Chrome |
| Chunking | Token-aware chunking with `tiktoken` |
| Embeddings | `sentence-transformers` embedding model |
| Vector storage | Local NumPy index in `data/np_index/` |
| Retrieval | Brute-force cosine similarity over normalized embeddings |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers` |
| Guardrails | Topic check before retrieval, score check after retrieval |
| LLM | Groq chat completion model with fallback model support |
| Flask backend | `ui/app.py`, used by the React frontend proxy |
| FastAPI backend | `api/main.py`, useful for API docs and direct testing |
| Frontend | React + Vite + Tailwind CSS in `frontend-js/` |
| Evaluation | Custom retrieval evaluation with Hit Rate@k and MRR |

## Project Structure

```text
shopify-rag-assistant/
├── api/
│   └── main.py                  # FastAPI API
├── data/
│   ├── raw/                     # scraped Shopify article text
│   ├── chunks.json              # processed chunks
│   ├── np_index/                # embeddings.npy, metadata.json, config.json
│   └── eval_results/            # evaluator outputs
├── frontend-js/                 # separate React/Vite frontend
│   ├── src/
│   │   ├── components/          # chat UI, source cards, states, sidebar
│   │   ├── hooks/               # chat state hook
│   │   ├── pages/               # Home page
│   │   ├── services/            # API calls to /query and /health
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── golden_set/
│   └── questions.json           # retrieval evaluation questions
├── src/
│   ├── scraper.py               # scrape Shopify docs
│   ├── chunker.py               # convert raw docs into chunks
│   ├── embedder.py              # build the local NumPy vector index
│   ├── retriever.py             # cosine retrieval
│   ├── reranker.py              # cross-encoder reranking
│   ├── guardrails.py            # topic and score guardrails
│   ├── generator.py             # Groq answer generation
│   ├── pipeline.py              # end-to-end RAG orchestration
│   └── evaluator.py             # Hit Rate + MRR evaluation
├── ui/
│   ├── app.py                   # Flask backend + legacy UI route
│   └── templates/index.html     # legacy Flask HTML template
├── requirements.txt
└── README.md
```

## Backend Setup

Create and activate a Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root. This repo currently does not include a `.env.example`, so use the following as a starting point:

```env
GROQ_API_KEY_1=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_MODEL_FALLBACK=llama-3.1-8b-instant

EMBED_MODEL=all-MiniLM-L6-v2
TOP_K=5

RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANK_TOP_K=5

GUARDRAIL_MODEL=llama-3.3-70b-versatile
GUARDRAIL_SCORE_THRESHOLD=0.30

CHUNK_SIZE=400
CHUNK_OVERLAP=50
```

Notes:

- The scraper requires Chrome to be installed locally.
- The first run of the embedder or reranker can download `sentence-transformers` models.
- Groq keys can be provided as `GROQ_API_KEY_1`, `GROQ_API_KEY_2`, and so on, or as a single `GROQ_API_KEY`.

## RAG Data Pipeline

Run these commands from the repository root after activating the Python environment.

### 1. Scrape Shopify Docs

```bash
python src/scraper.py
```

Writes raw article `.txt` files under `data/raw/` and a manifest at `data/raw/manifest.json`.

### 2. Chunk Articles

```bash
python src/chunker.py
```

Reads `data/raw/**/*.txt` and writes `data/chunks.json`. Heading markers from scraped pages are used so chunks keep useful section context.

### 3. Generate Embeddings

```bash
python src/embedder.py
```

Creates the local NumPy index:

```text
data/np_index/embeddings.npy
data/np_index/metadata.json
data/np_index/config.json
```

### 4. Test Retrieval

```bash
python src/retriever.py
```

Runs sample queries and prints the top cosine-similarity matches.

### 5. Test Reranking

```bash
python src/reranker.py
```

Runs a smoke test that compares original cosine scores with cross-encoder rerank scores.

### 6. Test Guardrails

```bash
python src/guardrails.py
```

Runs topic and score-threshold guardrail checks. The topic guardrail uses a keyword fast-pass and fails open if the Groq check cannot run.

### 7. Test End-to-End RAG

```bash
python src/pipeline.py
```

Runs sample questions through the full flow: guardrails, retrieval, reranking, and generation.

### 8. Run Retrieval Evaluation

```bash
python src/evaluator.py
```

Evaluates retrieval over `golden_set/questions.json` and writes results under `data/eval_results/`.

Latest checked-in evaluation summary:

| Metric | Value |
|---|---:|
| Total questions | 25 |
| Hit Rate@1 | 88.0% |
| Hit Rate@3 | 96.0% |
| Hit Rate@5 | 96.0% |
| MRR | 0.92 |

## Backend Services

### Flask Backend

The React frontend is configured to proxy requests to the Flask app.

```bash
python ui/app.py
```

Flask runs at:

```text
http://localhost:5000
```

Available routes:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/` | Legacy Flask HTML UI |
| `GET` | `/health` | Health check used by the React frontend |
| `POST` | `/query` | Ask a Shopify question |

Example request:

```bash
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"How do I set up free shipping on Shopify?"}'
```

Example response shape:

```json
{
  "answer": "...",
  "sources": [
    {
      "title": "...",
      "url": "...",
      "heading": "...",
      "section": "...",
      "score": 0.5123,
      "rerank_score": 7.8912
    }
  ],
  "latency_ms": 423.0,
  "model": "llama-3.3-70b-versatile",
  "chunks_used": 5
}
```

### FastAPI Backend

```bash
uvicorn api.main:app --reload --port 8000
```

Open the interactive API docs:

```text
http://localhost:8000/docs
```

Available routes:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/query` | Ask a Shopify question |
| `GET` | `/stats` | Intended stats endpoint |

Note: `/stats` currently references an older Chroma-style `collection` attribute. The active retriever uses the local NumPy index, so update `/stats` before relying on it.

## Separate Frontend App

The frontend is a separate React/Vite application in `frontend-js/`. It is not bundled into the Python backend during development. Run it in its own terminal while the Flask backend runs in another terminal.

### Frontend Tech Stack

| Area | Tool |
|---|---|
| Framework | React 18 |
| Build tool | Vite |
| Styling | Tailwind CSS |
| Icons | `lucide-react` |
| Animations | `framer-motion` |
| Markdown answers | `react-markdown` + `remark-gfm` |

### Frontend Setup

```bash
cd frontend-js
npm install
```

### Run Frontend Locally

Terminal 1, start the backend:

```bash
python ui/app.py
```

Terminal 2, start the frontend:

```bash
cd frontend-js
npm run dev
```

Open the Vite URL, usually:

```text
http://localhost:5173
```

The frontend calls:

| Frontend call | Proxied backend route |
|---|---|
| `GET /health` | `http://localhost:5000/health` |
| `POST /query` | `http://localhost:5000/query` |

### Build Frontend

```bash
cd frontend-js
npm run build
```

The production build is emitted to:

```text
frontend-js/dist/
```

Preview the production build locally:

```bash
cd frontend-js
npm run preview
```

### Frontend Features

- Responsive chat layout with sidebar
- Suggested starter questions
- Chat message history during the current session
- Markdown rendering for assistant answers
- Source cards for cited Shopify docs
- Copy-answer action
- Loading and error states
- Backend health detection
- Light and dark theme toggle persisted in `localStorage`

## Query Flow Details

`src/pipeline.py` coordinates the full backend flow:

1. `check_topic(question)` blocks clearly off-topic questions before retrieval.
2. `Retriever.retrieve(question, top_k=10)` fetches candidate chunks.
3. Empty retrieval results return a friendly no-docs response.
4. `check_score(chunks[0]["score"])` blocks low-confidence retrieval.
5. `Reranker.rerank(question, chunks, top_k=5)` reorders candidates by cross-encoder relevance.
6. `Generator.generate(question, chunks)` builds a grounded answer from the reranked chunks.
7. The response includes sources, chunks used, latency, model, and guardrail metadata inside the pipeline result.

The Flask and FastAPI route handlers return the public fields needed by their current clients.

## Evaluation Methodology

`src/evaluator.py` evaluates retrieval quality rather than final answer quality.

A retrieved chunk is counted as a hit when:

- its `section` matches the expected section, or
- its title/text contains at least two expected keywords.

Metrics:

| Metric | Description |
|---|---|
| Hit Rate@1 | Percentage of questions with a hit in the top result |
| Hit Rate@3 | Percentage of questions with a hit in the top 3 |
| Hit Rate@5 | Percentage of questions with a hit in the top 5 |
| MRR | Mean reciprocal rank of the first hit |

## Troubleshooting

| Problem | What to check |
|---|---|
| `No Groq API keys found` | Add `GROQ_API_KEY_1` or `GROQ_API_KEY` to `.env` |
| Frontend says backend is unavailable | Make sure `python ui/app.py` is running on port 5000 |
| Model download is slow | The first `sentence-transformers` run may download embedding or reranker models |
| Scraper fails to start | Confirm Chrome is installed and Selenium dependencies are available |
| FastAPI `/stats` fails | The endpoint still references an older Chroma-style collection |
| Poor retrieval results | Re-run scrape, chunking, embedding, then evaluation |

## Important Implementation Notes

- The active vector store is `data/np_index/`, not ChromaDB.
- Retrieval is exact brute-force NumPy cosine similarity, which is reasonable for the current dataset size.
- Reranking improves context quality by scoring the question and chunk together.
- Guardrails are designed to fail open when the topic-check LLM call fails.
- The React frontend lives in `frontend-js/`; older README references to `frontend/` are not current.
- The legacy Flask HTML UI remains available through `ui/templates/index.html`.

## Production Scaling Path

Recommended next steps:

1. Update FastAPI `/stats` for the NumPy retriever.
2. Return guardrail metadata through API schemas if frontend display needs it.
3. Add structured logs, request IDs, latency metrics, and token/cost tracking.
4. Add authentication and rate limiting.
5. Add answer-groundedness evaluation in addition to retrieval evaluation.
6. Add hybrid retrieval if the corpus grows.
7. Move from local NumPy search to FAISS, HNSW, pgvector, Pinecone, or Weaviate for larger corpora.
8. Add deployment packaging for the Python backend and `frontend-js` production build.
