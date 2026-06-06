# MoodTunes AI – FastAPI Application (Groq + local ChromaDB, no Docker)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import recommend, feedback, health, songs
from database.db import init_db
from rag.vector_store import VectorStore
from embeddings.embedding_service import EmbeddingService
from config import GROQ_API_KEY


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[MoodTunes] Starting up...")
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        print("⚠  GROQ_API_KEY not set! Copy .env.example → .env and add your key.")
        print("   Get a free key at: https://console.groq.com")
    await init_db()
    await VectorStore.connect()
    await EmbeddingService.warmup()   # downloads model on first run (~90 MB)
    print("[MoodTunes] Ready at http://localhost:8000")
    print("[MoodTunes] Docs at  http://localhost:8000/docs")
    yield
    print("[MoodTunes] Shutting down.")


app = FastAPI(
    title="MoodTunes AI API",
    version="2.0.0",
    description="Groq-powered music recommendation backend — runs locally, no Docker needed",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*", "http://127.0.0.1:*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,    prefix="/api/v1", tags=["health"])
app.include_router(recommend.router, prefix="/api/v1", tags=["recommend"])
app.include_router(feedback.router,  prefix="/api/v1", tags=["feedback"])
app.include_router(songs.router,     prefix="/api/v1", tags=["songs"])


@app.get("/")
async def root():
    return {
        "service": "MoodTunes AI",
        "version": "2.0.0",
        "stack": "Groq API + sentence-transformers + ChromaDB (local)",
        "docs": "http://localhost:8000/docs",
    }
