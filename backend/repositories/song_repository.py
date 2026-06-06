# MoodTunes AI – Song Repository (Repository Pattern)
# Abstracts all song-related DB operations

import json
from database.db import get_db
from models.schemas import SongSchema


class SongRepository:
    @staticmethod
    async def get_by_id(song_id: str) -> dict | None:
        async with get_db() as db:
            row = await db.fetchone(
                "SELECT * FROM songs WHERE song_id = ?", (song_id,)
            )
            if not row:
                return None
            return SongRepository._row_to_dict(row)

    @staticmethod
    async def get_many(song_ids: list[str]) -> list[dict]:
        if not song_ids:
            return []
        placeholders = ",".join("?" * len(song_ids))
        async with get_db() as db:
            rows = await db.fetchall(
                f"SELECT * FROM songs WHERE song_id IN ({placeholders})", tuple(song_ids)
            )
            return [SongRepository._row_to_dict(r) for r in rows]

    @staticmethod
    async def upsert(song: dict):
        async with get_db() as db:
            await db.execute(
                """INSERT OR REPLACE INTO songs
                   (song_id, title, artist, genre, energy_level, mood_tags,
                    context_tags, lyrics_summary, youtube_url, playlist_url)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    song["song_id"], song["title"], song["artist"],
                    song.get("genre", ""), song.get("energy_level", "medium"),
                    json.dumps(song.get("mood_tags", [])),
                    json.dumps(song.get("context_tags", [])),
                    song.get("lyrics_summary", ""),
                    song.get("youtube_url", ""),
                    song.get("playlist_url"),
                )
            )

    @staticmethod
    async def count() -> int:
        async with get_db() as db:
            row = await db.fetchone("SELECT COUNT(*) as cnt FROM songs")
            return row["cnt"] if row else 0

    @staticmethod
    async def search_by_genre(genre: str, limit: int = 20) -> list[dict]:
        async with get_db() as db:
            rows = await db.fetchall(
                "SELECT * FROM songs WHERE genre LIKE ? LIMIT ?",
                (f"%{genre}%", limit)
            )
            return [SongRepository._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(row) -> dict:
        d = dict(row)
        for field in ("mood_tags", "context_tags"):
            if isinstance(d.get(field), str):
                try:
                    d[field] = json.loads(d[field])
                except Exception:
                    d[field] = []
        return d
