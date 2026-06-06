# MoodTunes AI – User Repository (Repository Pattern)
import json
from database.db import get_db


class UserRepository:
    @staticmethod
    async def get_or_create(user_id: str) -> dict:
        async with get_db() as db:
            row = await db.fetchone(
                "SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)
            )
            if not row:
                await db.execute(
                    "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
                )
                await db.execute(
                    "INSERT OR IGNORE INTO user_preferences (user_id) VALUES (?)", (user_id,)
                )
                return {"user_id": user_id}
            return dict(row)

    @staticmethod
    async def get_feedback_summary(user_id: str) -> dict:
        """Returns counts of each action type for a user."""
        async with get_db() as db:
            rows = await db.fetchall(
                """SELECT action, COUNT(*) as cnt
                   FROM feedback WHERE user_id = ?
                   GROUP BY action""",
                (user_id,)
            )
            return {r["action"]: r["cnt"] for r in rows}

    @staticmethod
    async def get_recommendation_history(user_id: str, limit: int = 50) -> list[dict]:
        async with get_db() as db:
            rows = await db.fetchall(
                """SELECT * FROM recommendation_history
                   WHERE user_id = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (user_id, limit)
            )
            return [dict(r) for r in rows]

    @staticmethod
    async def record_recommendation(user_id: str, song_id: str,
                                     emotion: str, context: str,
                                     intent: str, confidence: int):
        async with get_db() as db:
            await db.execute(
                """INSERT INTO recommendation_history
                   (user_id, song_id, emotion, context, intent, confidence)
                   VALUES (?,?,?,?,?,?)""",
                (user_id, song_id, emotion, context, intent, confidence)
            )

    @staticmethod
    async def get_top_genres(user_id: str, limit: int = 5) -> list[str]:
        async with get_db() as db:
            rows = await db.fetchall(
                """SELECT genre FROM genre_scores
                   WHERE user_id = ? AND score > 0
                   ORDER BY score DESC LIMIT ?""",
                (user_id, limit)
            )
            return [r["genre"] for r in rows]

    @staticmethod
    async def delete_user_data(user_id: str):
        """GDPR-style data deletion."""
        async with get_db() as db:
            for table in ["user_preferences", "genre_scores",
                          "feedback", "recommendation_history",
                          "conversation_snapshots", "settings"]:
                await db.execute(
                    f"DELETE FROM {table} WHERE user_id = ?", (user_id,)
                )
