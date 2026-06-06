# MoodTunes AI – Health check (Groq version, no Ollama)
from fastapi import APIRouter
from rag.vector_store import VectorStore
from groq import AsyncGroq
from config import GROQ_API_KEY, GROQ_MODEL

router = APIRouter()

@router.get("/health")
async def health():
    groq_ok = False
    try:
        client = AsyncGroq(api_key=GROQ_API_KEY)
        await client.models.list()
        groq_ok = True
    except Exception:
        pass

    song_count = VectorStore.count()
    return {
        "status": "ok",
        "groq_api": groq_ok,
        "groq_model": GROQ_MODEL,
        "chromadb": "local",
        "song_count": song_count,
        "embeddings": "sentence-transformers (local)",
    }
