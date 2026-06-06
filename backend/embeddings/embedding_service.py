# MoodTunes AI – Local Embedding Service (sentence-transformers, no API key)
# Uses all-MiniLM-L6-v2 (~90MB) which runs on CPU.
# No Ollama, no Docker, no internet required after first model download.

from __future__ import annotations
import asyncio
from functools import lru_cache
from config import EMBEDDING_MODEL

_model = None          # lazy-loaded on first use
_cache: dict[str, list[float]] = {}
MAX_CACHE = 2000


def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"[Embeddings] Loading {EMBEDDING_MODEL}...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"[Embeddings] Model ready. Dimension: {_model.get_sentence_embedding_dimension()}")
    return _model


class EmbeddingService:

    @classmethod
    async def warmup(cls):
        """Pre-load the model in a thread pool so startup isn't blocked."""
        await asyncio.to_thread(_load_model)

    @classmethod
    async def embed(cls, text: str) -> list[float]:
        if text in _cache:
            return _cache[text]
        vec = await asyncio.to_thread(cls._embed_sync, text)
        if len(_cache) >= MAX_CACHE:
            del _cache[next(iter(_cache))]
        _cache[text] = vec
        return vec

    @staticmethod
    def _embed_sync(text: str) -> list[float]:
        model = _load_model()
        return model.encode(text).tolist()

    @classmethod
    async def embed_song(cls, song: dict) -> list[float]:
        text = (
            f"{song['title']} by {song['artist']}. "
            f"Genre: {song.get('genre', '')}. "
            f"Energy: {song.get('energy_level', '')}. "
            f"Mood: {_join(song.get('mood_tags', []))}. "
            f"Context: {_join(song.get('context_tags', []))}. "
            f"{song.get('lyrics_summary', '')}"
        )
        return await cls.embed(text)

    @classmethod
    async def embed_query(cls, emotion: str, context: str, intent: str,
                          favorite_genres: list[str]) -> list[float]:
        genres = ", ".join(favorite_genres[:3]) if favorite_genres else ""
        text = (
            f"Music for someone feeling {emotion} "
            f"in a {context} situation who needs {intent}. "
            + (f"They prefer {genres}." if genres else "")
        )
        return await cls.embed(text)


def _join(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value) if value else ""
