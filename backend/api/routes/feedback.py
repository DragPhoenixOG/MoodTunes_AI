# MoodTunes AI – /feedback route
from fastapi import APIRouter
from models.schemas import FeedbackRequest
from memory.memory_engine import MemoryEngine
from database.db import get_db

router = APIRouter()


@router.post("/feedback")
async def feedback(req: FeedbackRequest):
    # Fetch song metadata for genre/artist info
    genre = artist = ""
    async with get_db() as db:
        row = await db.fetchone("SELECT genre, artist FROM songs WHERE song_id = ?", (req.song_id,))
        if row:
            genre = row["genre"] or ""
            artist = row["artist"] or ""
        await db.execute(
            "INSERT INTO feedback (user_id, song_id, action) VALUES (?, ?, ?)",
            (req.user_id, req.song_id, req.action)
        )

    await MemoryEngine.record_feedback(req.user_id, req.song_id, req.action, genre, artist)
    return {"ok": True}
