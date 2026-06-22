"""
api/main.py
───────────
FastAPI backend exposing the RAG pipeline as a REST API.

Endpoints:
    POST /query          → ask a question, get an answer + sources
    GET  /health         → health check
    GET  /stats          → collection stats

Usage:
    cd shopify-rag-assistant
    uvicorn api.main:app --reload --port 8000
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from pipeline import RAGPipeline

# ── App setup ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Shopify RAG Assistant API",
    description="Ask natural language questions about running a Shopify store.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init pipeline once at startup (loads model + connects to ChromaDB)
pipeline: RAGPipeline = None

@app.on_event("startup")
async def startup():
    global pipeline
    pipeline = RAGPipeline()
    print("[API] RAGPipeline ready ✓")


# ── Request / Response models ─────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500,
                          example="How do I set up free shipping on Shopify?")
    top_k: int    = Field(default=5, ge=1, le=10)

class SourceItem(BaseModel):
    title: str
    url:   str

class QueryResponse(BaseModel):
    question:    str
    answer:      str
    sources:     list[SourceItem]
    latency_ms:  float
    model:       str
    chunks_used: int


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "pipeline_ready": pipeline is not None}


@app.get("/stats")
def stats():
    if not pipeline:
        raise HTTPException(503, "Pipeline not ready")
    count = pipeline.retriever.collection.count()
    return {
        "chunks_in_db": count,
        "embed_model":  os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2"),
        "llm_model":    os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "collection":   os.getenv("CHROMA_COLLECTION", "shopify_docs"),
    }


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if not pipeline:
        raise HTTPException(503, "Pipeline not ready")
    try:
        result = pipeline.query(req.question, top_k=req.top_k)
        return QueryResponse(
            question    = result["question"],
            answer      = result["answer"],
            sources     = result["sources"],
            latency_ms  = result["latency_ms"],
            model       = result["model"],
            chunks_used = result["chunks_used"],
        )
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {str(e)}")
