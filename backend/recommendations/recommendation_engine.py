# MoodTunes AI – Hybrid Recommendation Engine
#
# Scoring weights:
#   Emotion match   40%
#   Context match   25%
#   Intent match    15%
#   User history    20%

from models.schemas import (
    EmotionResult, ContextResult, IntentResult,
    UserMemory, RecommendationOutput,
)
from rag.vector_store import VectorStore
from embeddings.embedding_service import EmbeddingService
from services.youtube_service import YouTubeService

# ── Mapping tables ────────────────────────────────────────────────────────────

EMOTION_TO_MOOD: dict[str, list[str]] = {
    "happy":        ["happy", "cheerful", "uplifting"],
    "sad":          ["sad", "melancholic", "emotional"],
    "motivated":    ["motivational", "empowering", "energetic"],
    "excited":      ["excited", "euphoric", "party"],
    "confident":    ["confident", "powerful", "triumphant"],
    "anxious":      ["calming", "soothing", "ambient"],
    "focused":      ["focus", "study", "concentration"],
    "burned_out":   ["relaxing", "chill", "lo-fi"],
    "romantic":     ["romantic", "love", "sweet"],
    "heartbroken":  ["heartbreak", "sad", "lonely"],
    "relaxed":      ["chill", "relaxed", "peaceful"],
    "angry":        ["intense", "aggressive", "metal"],
    "celebratory":  ["celebration", "party", "joyful"],
    "productive":   ["focus", "productivity", "upbeat"],
    "workout":      ["workout", "energetic", "pump"],
}

INTENT_TO_MOOD: dict[str, list[str]] = {
    "Need Motivation":   ["motivational", "empowering"],
    "Need Focus":        ["focus", "concentration"],
    "Need Confidence":   ["confident", "powerful"],
    "Need Relaxation":   ["relaxing", "calming"],
    "Need Energy":       ["energetic", "upbeat"],
    "Need Comfort":      ["comforting", "warm"],
    "Need Recovery":     ["healing", "peaceful"],
    "Need Inspiration":  ["inspiring", "uplifting"],
    "Need Celebration":  ["celebration", "party"],
}


class RecommendationEngine:
    @staticmethod
    async def recommend(
        emotion: EmotionResult,
        context: ContextResult,
        intent: IntentResult,
        memory: UserMemory,
        user_id: str,
    ) -> RecommendationOutput | None:

        # 1. Generate query embedding from blended signals
        query_vec = await EmbeddingService.embed_query(
            emotion=emotion.emotion,
            context=context.context,
            intent=intent.intent,
            favorite_genres=memory.favorite_genres,
        )

        # 2. Retrieve top-20 candidates from ChromaDB
        candidates = VectorStore.query(query_vec, n_results=20)
        if not candidates:
            return None

        # 3. Hybrid scoring
        scored = []
        for song in candidates:
            score = RecommendationEngine._score(song, emotion, context, intent, memory)
            scored.append((score, song))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_song = scored[0]

        # 4. Build output
        song_title  = best_song.get("title", "Unknown")
        artist      = best_song.get("artist", "Unknown")
        song_id     = best_song["song_id"]
        youtube_url = YouTubeService.build_url(song_title, artist)
        playlist_url = best_song.get("playlist_url") or YouTubeService.build_playlist_url(
            emotion.emotion, context.context
        )

        reason = RecommendationEngine._reason(
            best_song, emotion, context, intent, memory
        )
        confidence = min(int(best_score * 100), 99)

        return RecommendationOutput(
            song=song_title,
            artist=artist,
            song_id=song_id,
            confidence=confidence,
            reason=reason,
            youtube_url=youtube_url,
            playlist_url=playlist_url,
        )

    @staticmethod
    def _score(
        song: dict,
        emotion: EmotionResult,
        context: ContextResult,
        intent: IntentResult,
        memory: UserMemory,
    ) -> float:
        mood_tags    = _parse_list(song.get("mood_tags", ""))
        context_tags = _parse_list(song.get("context_tags", ""))
        genre        = song.get("genre", "").lower()
        artist       = song.get("artist", "").lower()
        song_id      = song.get("song_id", "")

        # Penalise disliked songs hard
        if song_id in memory.disliked_songs:
            return 0.0
        # Penalise recently played
        if song_id in memory.recent_recommendations[-5:]:
            return 0.01

        # ── Emotion match (40%) ───────────────────────────────────────────────
        target_moods = set(EMOTION_TO_MOOD.get(emotion.emotion, []))
        em_score = len(target_moods & set(mood_tags)) / max(len(target_moods), 1)

        # ── Context match (25%) ───────────────────────────────────────────────
        ctx_score = 1.0 if context.context in context_tags else 0.0

        # ── Intent match (15%) ───────────────────────────────────────────────
        intent_moods = set(INTENT_TO_MOOD.get(intent.intent, []))
        intent_score = len(intent_moods & set(mood_tags)) / max(len(intent_moods), 1)

        # ── User history match (20%) ──────────────────────────────────────────
        history_score = 0.0
        if genre in [g.lower() for g in memory.preferred_genres]:
            history_score += 0.5
        if genre in [g.lower() for g in memory.favorite_genres]:
            history_score += 0.3
        if artist in [a.lower() for a in memory.favorite_artists]:
            history_score += 0.2
        if song_id in memory.liked_songs:
            history_score = min(history_score + 0.4, 1.0)
        history_score = min(history_score, 1.0)

        final = (
            em_score      * 0.40 +
            ctx_score     * 0.25 +
            intent_score  * 0.15 +
            history_score * 0.20
        )
        # Add small vector similarity bonus (1 - cosine distance)
        distance = song.get("distance", 0.5)
        final += (1 - distance) * 0.05
        return min(final, 1.0)

    @staticmethod
    def _reason(song, emotion, context, intent, memory) -> str:
        song_title = song.get("title", "this song")
        artist     = song.get("artist", "the artist")
        genre      = song.get("genre", "")
        fav        = memory.favorite_genres

        parts = []
        if fav and genre.lower() in [g.lower() for g in fav]:
            parts.append(f"matches your preferred {genre} taste")
        parts.append(f"suited for {emotion.emotion.replace('_', ' ')} feelings")
        if context.context != "general":
            parts.append(f"aligns with your {context.context} situation")
        parts.append(f"helps you {intent.intent.lower()}")

        return f"{song_title} by {artist}: " + ", and ".join(parts[:3]) + "."


def _parse_list(value) -> list[str]:
    if isinstance(value, list):
        return [v.lower() for v in value]
    if isinstance(value, str):
        return [v.strip().lower() for v in value.strip("[]").replace("'", "").split(",") if v.strip()]
    return []
