# MoodTunes AI – Backend Notification Logger
# Tracks notification delivery and engagement for analytics

from database.db import get_db


class NotificationLogger:
    @staticmethod
    async def log_sent(user_id: str, song_id: str, emotion: str, context: str):
        async with get_db() as db:
            await db.execute(
                """INSERT INTO recommendation_history
                   (user_id, song_id, emotion, context, intent, confidence)
                   VALUES (?, ?, ?, ?, 'auto', 0)""",
                (user_id, song_id, emotion, context)
            )

    @staticmethod
    async def get_engagement_rate(user_id: str) -> float:
        """Ratio of played/liked to total recommendations."""
        async with get_db() as db:
            total_row = await db.fetchone(
                "SELECT COUNT(*) as cnt FROM recommendation_history WHERE user_id = ?",
                (user_id,)
            )
            engaged_row = await db.fetchone(
                """SELECT COUNT(*) as cnt FROM feedback
                   WHERE user_id = ? AND action IN ('play','like','playlist')""",
                (user_id,)
            )
        total = total_row["cnt"] if total_row else 0
        engaged = engaged_row["cnt"] if engaged_row else 0
        return round(engaged / total, 2) if total > 0 else 0.0
