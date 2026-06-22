# 🛍️ Shopify RAG Assistant

> An AI-powered Research Assistant for Shopify store operators.  
> Ask natural language questions — get grounded answers from official Shopify documentation.

---

## 📌 Overview

This project demonstrates a **production-ready RAG (Retrieval-Augmented Generation) pipeline**
built on top of Shopify's public Help Center documentation.

| Component | Tool |
|---|---|
| Data Source | Shopify Help Center (scraped via BeautifulSoup) |
| Chunking | Token-aware sliding window (tiktoken) |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) |
| Vector Store | ChromaDB (persistent, local) |
| LLM | Llama-3.3-70B via Groq API |
| API | FastAPI |
| UI | Gradio |
| Evaluation | Custom: Hit Rate@k + MRR |

---

## 🗂️ Project Structure

```
shopify-rag-assistant/
├── data/
│   ├── raw/                  ← scraped Shopify help articles
│   ├── chunks.json           ← all chunks after processing
│   ├── chroma_db/            ← ChromaDB vector store (auto-created)
│   └── eval_results/         ← evaluation CSVs and JSONs
├── src/
│   ├── scraper.py            ← crawl Shopify help center
│   ├── chunker.py            ← chunk + clean text
│   ├── embedder.py           ← embed + store in ChromaDB
│   ├── retriever.py          ← cosine similarity retrieval
│   ├── generator.py          ← Groq LLM answer generation
│   ├── pipeline.py           ← end-to-end RAG pipeline
│   └── evaluator.py          ← Hit Rate + MRR evaluation
├── golden_set/
│   └── questions.json        ← 25 evaluation questions
├── api/
│   └── main.py               ← FastAPI REST API
├── ui/
│   └── app.py                ← Gradio chat interface
├── report/
│   └── recommendation.md     ← Architecture & tool comparison report
├── diagrams/                 ← architecture diagrams
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Clone & create virtual environment
```bash
git clone <your-repo-url>
cd shopify-rag-assistant
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and add your Groq API key(s)
```

Get free Groq API keys at: https://console.groq.com

---

## 🚀 Running the Pipeline

Run each step in order from the project root:

### Step 1 — Scrape Shopify Help Center
```bash
python src/scraper.py
```
Downloads ~80–100 articles across 10 sections into `data/raw/`.

### Step 2 — Chunk articles
```bash
python src/chunker.py
```
Produces `data/chunks.json` with token-aware chunks + metadata.

### Step 3 — Embed + store in ChromaDB
```bash
python src/embedder.py
```
Embeds all chunks locally and persists to `data/chroma_db/`.

### Step 4 — Test retrieval
```bash
python src/retriever.py
```
Runs 5 test queries and prints top-3 results per query.

### Step 5 — Test full pipeline
```bash
python src/pipeline.py
```
Runs 5 demo questions end-to-end (retrieve → generate → answer).

### Step 6 — Run evaluation
```bash
python src/evaluator.py
```
Evaluates Hit Rate@1/3/5 and MRR over 25 golden questions.
Results saved to `data/eval_results/`.

---

## 🌐 Running the API

```bash
uvicorn api.main:app --reload --port 8000
```

Then open: http://localhost:8000/docs (interactive Swagger UI)

**Endpoints:**
- `POST /query` — ask a question
- `GET /health` — health check
- `GET /stats` — collection stats

**Example request:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I set up free shipping?", "top_k": 5}'
```

---

## 🖥️ Running the Chat UI

```bash
python ui/app.py
```

Open: http://localhost:7860

---

## 📊 Evaluation Metrics

| Metric | Description |
|---|---|
| Hit Rate@1 | % of questions where top result is relevant |
| Hit Rate@3 | % of questions where correct answer in top 3 |
| Hit Rate@5 | % of questions where correct answer in top 5 |
| MRR | Mean Reciprocal Rank — average of 1/rank of first hit |

---

## 💰 Estimated Infrastructure Cost

| Component | Cost |
|---|---|
| Groq API (Llama-3.3-70B) | ~$0.00059/1K input tokens (free tier available) |
| sentence-transformers embedding | Free (runs locally) |
| ChromaDB | Free (open source, runs locally) |
| FastAPI / Gradio | Free (self-hosted) |
| **Total for 1000 queries/day** | **~$0.50–$2/month** |

For production scale (100K queries/day), estimated $50–200/month with Groq.

---

## 🔮 Production Scaling Path

1. **Vector DB** → migrate ChromaDB → Pinecone or Weaviate for distributed search
2. **Embeddings** → switch to OpenAI `text-embedding-3-small` for higher quality
3. **LLM** → add Claude/GPT-4o as fallback, route by query complexity
4. **Cache** → Redis semantic cache for repeated questions
5. **Monitoring** → log every query + latency + hit rate in production

---

## 🛠️ Tech Stack Comparison (Part 1 — see report/ for full analysis)

| Tool | Category | Why chosen |
|---|---|---|
| ChromaDB | Vector DB | Zero setup, embedded, perfect for POC |
| Pinecone | Vector DB (prod) | Managed, scales to millions of vectors |
| Weaviate | Vector DB (prod) | Open source, hybrid search support |
| Groq | LLM Provider | Fastest inference, generous free tier |
| OpenAI | LLM Provider | Highest quality, industry standard |
| sentence-transformers | Embeddings | Free, runs locally, surprisingly strong |
