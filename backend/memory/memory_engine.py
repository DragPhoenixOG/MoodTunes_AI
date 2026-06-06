# MoodTunes AI – Memory Engine
# Tracks user feedback, builds preference profile, improves recommendations over time

import json
from database.db import get_db
from models.schemas import UserMemory

GENRE_BOOST_LIKE    = 1.0
GENRE_BOOST_PLAY    = 0.5
GENRE_PENALISE_DISLIKE = -1.5
TOP_GENRES = 5
TOP_ARTISTS = 10
MAX_RECENT = 50


class MemoryEngine:
    @staticmethod
    async def get_memory(user_id: str) -> UserMemory:
        async with get_db() as db:
            row = await db.fetchone(
                "SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)
            )
            if not row:
                await MemoryEngine._create_user(db, user_id)
                return UserMemory(user_id=user_id)

            return UserMemory(
                user_id=user_id,
                liked_songs     = json.loads(row["liked_songs"] or "[]"),
                disliked_songs  = json.loads(row["disliked_songs"] or "[]"),
                favorite_artists= json.loads(row["favorite_artists"] or "[]"),
                favorite_genres = json.loads(row["favorite_genres"] or "[]"),
                recent_recommendations=json.loads(row["recent_recommendations"] or "[]"),
                preferred_genres= json.loads(row["preferred_genres"] or "[]"),
            )

    @staticmethod
    async def record_feedback(user_id: str, song_id: str, action: str,
                               genre: str = "", artist: str = ""):
        async with get_db() as db:
            mem = await MemoryEngine.get_memory(user_id)

            if action == "like":
                if song_id not in mem.liked_songs:
                    mem.liked_songs.insert(0, song_id)
                if song_id in mem.disliked_songs:
                    mem.disliked_songs.remove(song_id)
                if artist and artist not in mem.favorite_artists:
                    mem.favorite_artists.insert(0, artist)

            elif action == "dislike":
                if song_id not in mem.disliked_songs:
                    mem.disliked_songs.insert(0, song_id)
                if song_id in mem.liked_songs:
                    mem.liked_songs.remove(song_id)

            # Update genre scores
            if genre:
                await MemoryEngine._update_genre_score(db, user_id, genre, action)
                preferred = await MemoryEngine._top_genres(db, user_id)
                mem.preferred_genres = preferred

            await MemoryEngine._save(db, user_id, mem)

    @staticmethod
    async def record_recommendation(user_id: str, song_id: str):
        async with get_db() as db:
            mem = await MemoryEngine.get_memory(user_id)
            if song_id not in mem.recent_recommendations:
                mem.recent_recommendations.insert(0, song_id)
            mem.recent_recommendations = mem.recent_recommendations[:MAX_RECENT]
            await MemoryEngine._save(db, user_id, mem)

    # ─── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    async def _create_user(db, user_id: str):
        await db.execute(
            "INSERT OR IGNORE INTO user_preferences (user_id) VALUES (?)",
            (user_id,)
        )

    @staticmethod
    async def _save(db, user_id: str, mem: UserMemory):
        await db.execute(
            """INSERT INTO user_preferences (user_id, liked_songs, disliked_songs,
               favorite_artists, favorite_genres, recent_recommendations, preferred_genres)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET
                 liked_songs=excluded.liked_songs,
                 disliked_songs=excluded.disliked_songs,
                 favorite_artists=excluded.favorite_artists,
                 recent_recommendations=excluded.recent_recommendations,
                 preferred_genres=excluded.preferred_genres""",
            (
                user_id,
                json.dumps(mem.liked_songs[:200]),
                json.dumps(mem.disliked_songs[:200]),
                json.dumps(mem.favorite_artists[:TOP_ARTISTS]),
                json.dumps(mem.favorite_genres),
                json.dumps(mem.recent_recommendations),
                json.dumps(mem.preferred_genres),
            )
        )

    @staticmethod
    async def _update_genre_score(db, user_id: str, genre: str, action: str):
        delta = {
            "like": GENRE_BOOST_LIKE,
            "play": GENRE_BOOST_PLAY,
            "dislike": GENRE_PENALISE_DISLIKE,
        }.get(action, 0)
        if delta == 0:
            return
        await db.execute(
            """INSERT INTO genre_scores (user_id, genre, score)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, genre) DO UPDATE SET
                 score = score + excluded.score""",
            (user_id, genre.lower(), delta)
        )

    @staticmethod
    async def _top_genres(db, user_id: str) -> list[str]:
        rows = await db.fetchall(
            """SELECT genre FROM genre_scores
               WHERE user_id = ? AND score > 0
               ORDER BY score DESC LIMIT ?""",
            (user_id, TOP_GENRES)
        )
        return [r["genre"] for r in rows]
