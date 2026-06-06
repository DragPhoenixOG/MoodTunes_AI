# MoodTunes AI – ChromaDB Vector Store (local persistent client, no server/Docker)
import chromadb
from chromadb.config import Settings
from config import CHROMA_PATH

COLLECTION_NAME = "songs"

_client: chromadb.ClientAPI | None = None
_collection = None


class VectorStore:
    @staticmethod
    async def connect():
        """Use a local persistent ChromaDB client — no server process needed."""
        global _client, _collection
        import os
        os.makedirs(CHROMA_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"[ChromaDB] Connected. Songs in DB: {_collection.count()}")

    @staticmethod
    async def disconnect():
        pass  # PersistentClient flushes automatically

    @staticmethod
    async def upsert_songs(songs: list[dict], embeddings: list[list[float]]):
        """Batch upsert songs with embeddings into ChromaDB."""
        _collection.upsert(
            ids=[s["song_id"] for s in songs],
            embeddings=embeddings,
            metadatas=[
                {k: (", ".join(v) if isinstance(v, list) else str(v or ""))
                 for k, v in s.items() if k != "song_id"}
                for s in songs
            ],
            documents=[
                f"{s['title']} by {s['artist']}. "
                f"Mood: {_j(s.get('mood_tags', []))}. "
                f"Context: {_j(s.get('context_tags', []))}. "
                f"{s.get('lyrics_summary', '')}"
                for s in songs
            ],
        )

    @staticmethod
    def query(query_embedding: list[float], n_results: int = 10) -> list[dict]:
        actual_n = min(n_results, _collection.count())
        if actual_n == 0:
            return []
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_n,
        )
        songs = []
        for i, meta in enumerate(results["metadatas"][0]):
            songs.append({
                "song_id": results["ids"][0][i],
                "distance": results["distances"][0][i],
                **meta,
            })
        return songs

    @staticmethod
    def count() -> int:
        try:
            return _collection.count() if _collection else 0
        except Exception:
            return 0


def _j(v) -> str:
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v) if v else ""
