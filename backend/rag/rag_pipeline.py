# MoodTunes AI – RAG Pipeline Orchestrator
#
# This module wires together:
#   1. Query embedding generation
#   2. ChromaDB vector retrieval
#   3. Metadata-based re-ranking
#   4. Personalisation filter
#
# It is used by the RecommendationEngine but can be tested independently.

from embeddings.embedding_service import EmbeddingService
from rag.vector_store import VectorStore
from models.schemas import EmotionResult, ContextResult, IntentResult, UserMemory


class RAGPipeline:
    def __init__(
        self,
        top_k_retrieval: int = 20,
        top_k_output: int = 5,
    ):
        self.top_k_retrieval = top_k_retrieval
        self.top_k_output = top_k_output

    async def retrieve(
        self,
        emotion: EmotionResult,
        context: ContextResult,
        intent: IntentResult,
        memory: UserMemory,
    ) -> list[dict]:
        """
        Full RAG retrieve-and-rank pipeline.
        Returns up to top_k_output candidate songs sorted by relevance.
        """
        # Step 1: Build rich query from detected signals
        query_vec = await EmbeddingService.embed_query(
            emotion=emotion.emotion,
            context=context.context,
            intent=intent.intent,
            favorite_genres=memory.preferred_genres or memory.favorite_genres,
        )

        # Step 2: Vector similarity search
        candidates = VectorStore.query(query_vec, n_results=self.top_k_retrieval)

        # Step 3: Remove hard-blocked songs (disliked)
        disliked = set(memory.disliked_songs)
        candidates = [c for c in candidates if c["song_id"] not in disliked]

        # Step 4: Soft de-duplicate recent plays
        recent = set((memory.recent_recommendations or [])[:10])
        fresh = [c for c in candidates if c["song_id"] not in recent]
        # Fall back to all candidates if everything was recently played
        pool = fresh if len(fresh) >= self.top_k_output else candidates

        # Step 5: Lightweight re-rank by tag overlap + cosine proximity
        ranked = sorted(
            pool,
            key=lambda s: self._quick_score(s, emotion, context, intent, memory),
            reverse=True,
        )

        return ranked[:self.top_k_output]

    # ── Internal helpers ────────────────────────────────────────────────────────

    def _quick_score(
        self,
        song: dict,
        emotion: EmotionResult,
        context: ContextResult,
        intent: IntentResult,
        memory: UserMemory,
    ) -> float:
        mood_tags    = self._to_set(song.get("mood_tags", ""))
        context_tags = self._to_set(song.get("context_tags", ""))
        genre        = (song.get("genre") or "").lower()
        distance     = song.get("distance", 0.5)

        # Cosine similarity (inverted distance)
        similarity = 1.0 - distance

        # Tag overlap bonuses
        emotion_bonus  = 0.3 if emotion.emotion.replace("_", "") in mood_tags else 0.0
        context_bonus  = 0.2 if context.context in context_tags else 0.0
        genre_bonus    = 0.15 if genre in [g.lower() for g in memory.favorite_genres] else 0.0
        liked_bonus    = 0.25 if song["song_id"] in memory.liked_songs else 0.0

        return similarity + emotion_bonus + context_bonus + genre_bonus + liked_bonus

    @staticmethod
    def _to_set(value) -> set[str]:
        if isinstance(value, list):
            return {v.lower().strip() for v in value}
        if isinstance(value, str):
            cleaned = value.strip("[]").replace("'", "").replace('"', "")
            return {v.strip().lower() for v in cleaned.split(",") if v.strip()}
        return set()
