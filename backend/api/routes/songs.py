# MoodTunes AI – Songs admin route
from fastapi import APIRouter, HTTPException
from models.schemas import SongSchema
from rag.vector_store import VectorStore
from embeddings.embedding_service import EmbeddingService
from database.db import get_db
import json

router = APIRouter()


@router.post("/songs/ingest")
async def ingest_songs(songs: list[SongSchema]):
    """Ingest songs into SQLite + ChromaDB."""
    dicts = [s.model_dump() for s in songs]

    # Generate embeddings
    embeddings = []
    for song in dicts:
        vec = await EmbeddingService.embed_song(song)
        embeddings.append(vec)

    # Store in vector DB
    await VectorStore.upsert_songs(dicts, embeddings)

    # Store in SQLite
    async with get_db() as db:
        for s in dicts:
            await db.execute(
                """INSERT OR REPLACE INTO songs
                   (song_id, title, artist, genre, energy_level, mood_tags,
                    context_tags, lyrics_summary, youtube_url, playlist_url)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    s["song_id"], s["title"], s["artist"], s["genre"],
                    s["energy_level"],
                    json.dumps(s["mood_tags"]), json.dumps(s["context_tags"]),
                    s["lyrics_summary"], s["youtube_url"], s.get("playlist_url"),
                )
            )

    return {"ingested": len(songs)}


@router.get("/songs/count")
async def count_songs():
    return {"count": VectorStore.count()}
