# MoodTunes AI – Database initialisation and async context manager
import aiosqlite
from contextlib import asynccontextmanager

DB_PATH = "./data/moodtunes.db"

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS songs (
    song_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    genre TEXT,
    energy_level TEXT,
    mood_tags TEXT,
    context_tags TEXT,
    lyrics_summary TEXT,
    youtube_url TEXT,
    playlist_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    liked_songs TEXT DEFAULT '[]',
    disliked_songs TEXT DEFAULT '[]',
    favorite_artists TEXT DEFAULT '[]',
    favorite_genres TEXT DEFAULT '[]',
    recent_recommendations TEXT DEFAULT '[]',
    preferred_genres TEXT DEFAULT '[]',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS genre_scores (
    user_id TEXT NOT NULL,
    genre TEXT NOT NULL,
    score REAL DEFAULT 0,
    PRIMARY KEY (user_id, genre)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    song_id TEXT NOT NULL,
    action TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    song_id TEXT NOT NULL,
    emotion TEXT,
    context TEXT,
    intent TEXT,
    confidence INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    source TEXT,
    text_hash TEXT,
    emotion TEXT,
    context TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    user_id TEXT PRIMARY KEY,
    cloud_mode INTEGER DEFAULT 0,
    notifications_enabled INTEGER DEFAULT 1,
    min_interval_seconds INTEGER DEFAULT 60,
    preferred_model TEXT DEFAULT 'llama3.2',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

_db_pool: aiosqlite.Connection | None = None


async def init_db():
    import os
    os.makedirs("./data", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES)
        await db.commit()
    print(f"[DB] Initialised at {DB_PATH}")


@asynccontextmanager
async def get_db():
    """Async context manager returning an augmented aiosqlite connection."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        yield _AsyncDB(conn)
        await conn.commit()


class _AsyncDB:
    """Thin helper so callers don't have to remember fetchall vs execute patterns."""
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def execute(self, sql: str, params=()):
        await self._conn.execute(sql, params)

    async def fetchone(self, sql: str, params=()):
        async with self._conn.execute(sql, params) as cur:
            return await cur.fetchone()

    async def fetchall(self, sql: str, params=()):
        async with self._conn.execute(sql, params) as cur:
            return await cur.fetchall()
