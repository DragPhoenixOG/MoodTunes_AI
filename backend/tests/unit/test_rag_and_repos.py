# MoodTunes AI – RAG + Repository Unit Tests (Groq edition)
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ─── RAG Pipeline ─────────────────────────────────────────────────────────────

class TestRAGPipeline:
    def _candidates(self, n=10):
        return [
            {"song_id": f"s{i}", "title": f"Song {i}", "artist": "Artist",
             "genre": "Rock", "mood_tags": ["motivational","energetic"],
             "context_tags": ["career"], "distance": 0.1 + i*0.05}
            for i in range(n)
        ]

    @pytest.mark.asyncio
    async def test_filters_disliked(self):
        from rag.rag_pipeline import RAGPipeline
        from models.schemas import EmotionResult, ContextResult, IntentResult, UserMemory
        with (
            patch("rag.rag_pipeline.EmbeddingService.embed_query",
                  new_callable=AsyncMock, return_value=[0.1]*384),
            patch("rag.rag_pipeline.VectorStore.query", return_value=self._candidates(10)),
        ):
            result = await RAGPipeline().retrieve(
                EmotionResult(emotion="motivated", confidence=90, reason=""),
                ContextResult(context="career", confidence=90),
                IntentResult(intent="Need Motivation"),
                UserMemory(user_id="u1", disliked_songs=["s0","s1","s2"]),
            )
        assert all(r["song_id"] not in ("s0","s1","s2") for r in result)

    @pytest.mark.asyncio
    async def test_returns_top_k(self):
        from rag.rag_pipeline import RAGPipeline
        from models.schemas import EmotionResult, ContextResult, IntentResult, UserMemory
        with (
            patch("rag.rag_pipeline.EmbeddingService.embed_query",
                  new_callable=AsyncMock, return_value=[0.1]*384),
            patch("rag.rag_pipeline.VectorStore.query", return_value=self._candidates(20)),
        ):
            result = await RAGPipeline(top_k_output=3).retrieve(
                EmotionResult(emotion="focused", confidence=85, reason=""),
                ContextResult(context="coding", confidence=85),
                IntentResult(intent="Need Focus"),
                UserMemory(user_id="u1"),
            )
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_empty_vector_store_returns_empty(self):
        from rag.rag_pipeline import RAGPipeline
        from models.schemas import EmotionResult, ContextResult, IntentResult, UserMemory
        with (
            patch("rag.rag_pipeline.EmbeddingService.embed_query",
                  new_callable=AsyncMock, return_value=[0.1]*384),
            patch("rag.rag_pipeline.VectorStore.query", return_value=[]),
        ):
            result = await RAGPipeline().retrieve(
                EmotionResult(emotion="happy", confidence=80, reason=""),
                ContextResult(context="general", confidence=80),
                IntentResult(intent="Need Relaxation"),
                UserMemory(user_id="u1"),
            )
        assert result == []


# ─── Quick Score internals ────────────────────────────────────────────────────

class TestQuickScore:
    def _song(self, mood_tags=None, genre="Rock", song_id="s1", distance=0.2):
        return {"song_id": song_id, "genre": genre,
                "mood_tags": mood_tags or ["motivational"],
                "context_tags": ["career"], "distance": distance}

    def test_liked_song_boosts_score(self):
        from rag.rag_pipeline import RAGPipeline
        from models.schemas import EmotionResult, ContextResult, IntentResult, UserMemory
        p = RAGPipeline()
        e = EmotionResult(emotion="motivated", confidence=90, reason="")
        c = ContextResult(context="career", confidence=90)
        i = IntentResult(intent="Need Motivation")
        song = self._song()
        plain  = p._quick_score(song, e, c, i, UserMemory(user_id="u1"))
        liked  = p._quick_score(song, e, c, i, UserMemory(user_id="u1", liked_songs=["s1"]))
        assert liked > plain

    def test_fav_genre_boosts_score(self):
        from rag.rag_pipeline import RAGPipeline
        from models.schemas import EmotionResult, ContextResult, IntentResult, UserMemory
        p = RAGPipeline()
        e = EmotionResult(emotion="happy", confidence=80, reason="")
        c = ContextResult(context="general", confidence=80)
        i = IntentResult(intent="Need Energy")
        song = self._song(genre="Rock")
        plain = p._quick_score(song, e, c, i, UserMemory(user_id="u1"))
        fav   = p._quick_score(song, e, c, i, UserMemory(user_id="u1", favorite_genres=["Rock"]))
        assert fav > plain

    def test_closer_distance_higher_score(self):
        from rag.rag_pipeline import RAGPipeline
        from models.schemas import EmotionResult, ContextResult, IntentResult, UserMemory
        p = RAGPipeline()
        e = EmotionResult(emotion="relaxed", confidence=80, reason="")
        c = ContextResult(context="general", confidence=80)
        i = IntentResult(intent="Need Relaxation")
        mem = UserMemory(user_id="u1")
        close = p._quick_score(self._song(distance=0.05), e, c, i, mem)
        far   = p._quick_score(self._song(distance=0.9),  e, c, i, mem)
        assert close > far


# ─── Song Repository helpers ──────────────────────────────────────────────────

class TestSongRepository:
    def test_parses_json_string_fields(self):
        from repositories.song_repository import SongRepository
        row = {"song_id":"s1","title":"T","artist":"A","genre":"Rock",
               "energy_level":"high",
               "mood_tags":'["happy","energetic"]',
               "context_tags":'["gym"]',
               "lyrics_summary":"","youtube_url":"","playlist_url":None}
        result = SongRepository._row_to_dict(row)
        assert isinstance(result["mood_tags"], list)
        assert "happy" in result["mood_tags"]
        assert "gym" in result["context_tags"]

    def test_passthrough_list_fields(self):
        from repositories.song_repository import SongRepository
        row = {"song_id":"s1","title":"T","artist":"A","genre":"R",
               "energy_level":"low",
               "mood_tags":["sad","emotional"],"context_tags":["breakup"],
               "lyrics_summary":"","youtube_url":"","playlist_url":None}
        result = SongRepository._row_to_dict(row)
        assert result["mood_tags"] == ["sad","emotional"]


# ─── Memory Engine helper ─────────────────────────────────────────────────────

class TestParseList:
    def test_list_input(self):
        from recommendations.recommendation_engine import _parse_list
        assert _parse_list(["Happy","SAD"]) == ["happy","sad"]

    def test_string_input(self):
        from recommendations.recommendation_engine import _parse_list
        result = _parse_list("['happy', 'chill']")
        assert "happy" in result and "chill" in result

    def test_empty_string(self):
        from recommendations.recommendation_engine import _parse_list
        assert _parse_list("") == []

    def test_empty_list(self):
        from recommendations.recommendation_engine import _parse_list
        assert _parse_list([]) == []


# ─── YouTube URL builder ──────────────────────────────────────────────────────

class TestYouTubeURLs:
    def test_song_url_encoded(self):
        from services.youtube_service import YouTubeService
        url = YouTubeService.build_url("Hall Of Fame", "The Script")
        assert "youtube.com/results?search_query=" in url
        assert "Hall" in url and "Script" in url

    def test_playlist_uses_context_first(self):
        from services.youtube_service import YouTubeService
        url = YouTubeService.build_playlist_url("motivated", "interview")
        assert "youtube.com" in url
        # interview context should yield interview-specific query
        assert "interview" in url.lower() or "confidence" in url.lower()

    def test_fallback_for_unknown_values(self):
        from services.youtube_service import YouTubeService
        url = YouTubeService.build_playlist_url("xyz_unknown", "xyz_context")
        assert "youtube.com" in url
        assert len(url) > 30
