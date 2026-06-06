# MoodTunes AI – Unit Tests (Groq edition)
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ─── Emotion Service (Groq) ────────────────────────────────────────────────────

class TestEmotionService:
    @pytest.mark.asyncio
    async def test_detect_returns_valid_emotion(self):
        import json
        from services.emotion_service import EmotionService

        mock_content = json.dumps({"emotion": "motivated", "confidence": 92,
                                   "reason": "Strong drive and determination."})
        mock_choice = MagicMock()
        mock_choice.message.content = mock_content
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        with patch.object(EmotionService, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
            mock_get.return_value = mock_client

            result = await EmotionService.detect("I'm going to crush this interview!")

        assert result.emotion == "motivated"
        assert result.confidence == 92

    @pytest.mark.asyncio
    async def test_detect_fallback_on_error(self):
        from services.emotion_service import EmotionService
        with patch.object(EmotionService, "_get_client", side_effect=Exception("No API key")):
            result = await EmotionService.detect("test text")
        assert result.emotion == "relaxed"
        assert result.confidence == 50

    @pytest.mark.asyncio
    async def test_detect_rejects_unknown_emotion(self):
        import json
        from services.emotion_service import EmotionService

        mock_content = json.dumps({"emotion": "unknown_emotion_xyz", "confidence": 80,
                                   "reason": "Something."})
        mock_choice = MagicMock()
        mock_choice.message.content = mock_content
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        with patch.object(EmotionService, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
            mock_get.return_value = mock_client
            result = await EmotionService.detect("blah blah")

        # Should fall back to "relaxed" for unknown emotions
        assert result.emotion == "relaxed"


# ─── Context Service (Groq) ────────────────────────────────────────────────────

class TestContextService:
    @pytest.mark.asyncio
    async def test_classify_interview(self):
        import json
        from services.context_service import ContextService

        mock_content = json.dumps({"context": "interview", "confidence": 95})
        mock_choice = MagicMock()
        mock_choice.message.content = mock_content
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        with patch.object(ContextService, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
            mock_get.return_value = mock_client
            result = await ContextService.classify("interview tomorrow morning")

        assert result.context == "interview"
        assert result.confidence == 95

    @pytest.mark.asyncio
    async def test_classify_fallback(self):
        from services.context_service import ContextService
        with patch.object(ContextService, "_get_client", side_effect=Exception("timeout")):
            result = await ContextService.classify("test")
        assert result.context == "general"


# ─── Recommendation Engine ─────────────────────────────────────────────────────

class TestRecommendationEngine:
    def _song(self, song_id="s1", mood_tags=None, context_tags=None,
               genre="Rock", distance=0.2):
        return {"song_id": song_id, "title": "Test Song", "artist": "Test Artist",
                "genre": genre, "energy_level": "high",
                "mood_tags": mood_tags or ["motivational", "empowering"],
                "context_tags": context_tags or ["career"], "distance": distance}

    def test_score_high_for_match(self):
        from recommendations.recommendation_engine import RecommendationEngine
        from models.schemas import EmotionResult, ContextResult, IntentResult, UserMemory
        song = self._song(mood_tags=["motivational","empowering","confident"],
                          context_tags=["career","interview"])
        score = RecommendationEngine._score(
            song,
            EmotionResult(emotion="motivated", confidence=90, reason=""),
            ContextResult(context="interview", confidence=90),
            IntentResult(intent="Need Confidence"),
            UserMemory(user_id="u1"),
        )
        assert score > 0.4

    def test_score_zero_for_disliked(self):
        from recommendations.recommendation_engine import RecommendationEngine
        from models.schemas import EmotionResult, ContextResult, IntentResult, UserMemory
        song = self._song(song_id="s_bad")
        score = RecommendationEngine._score(
            song,
            EmotionResult(emotion="happy", confidence=80, reason=""),
            ContextResult(context="general", confidence=80),
            IntentResult(intent="Need Relaxation"),
            UserMemory(user_id="u1", disliked_songs=["s_bad"]),
        )
        assert score == 0.0

    def test_favorite_genre_boosts(self):
        from recommendations.recommendation_engine import RecommendationEngine
        from models.schemas import EmotionResult, ContextResult, IntentResult, UserMemory
        song = self._song(genre="Rock")
        base = RecommendationEngine._score(
            song,
            EmotionResult(emotion="motivated", confidence=90, reason=""),
            ContextResult(context="career", confidence=90),
            IntentResult(intent="Need Motivation"),
            UserMemory(user_id="u1"),
        )
        boosted = RecommendationEngine._score(
            song,
            EmotionResult(emotion="motivated", confidence=90, reason=""),
            ContextResult(context="career", confidence=90),
            IntentResult(intent="Need Motivation"),
            UserMemory(user_id="u1", favorite_genres=["Rock"], preferred_genres=["Rock"]),
        )
        assert boosted > base


# ─── Embedding Service (sentence-transformers) ────────────────────────────────

class TestEmbeddingService:
    @pytest.mark.asyncio
    async def test_embed_returns_list(self):
        from embeddings.embedding_service import EmbeddingService
        with patch.object(EmbeddingService, "_embed_sync",
                          return_value=[0.1] * 384):
            vec = await EmbeddingService.embed("test text")
        assert isinstance(vec, list)
        assert len(vec) == 384

    @pytest.mark.asyncio
    async def test_embed_uses_cache(self):
        from embeddings.embedding_service import EmbeddingService, _cache
        _cache["cached_text"] = [0.5] * 384
        vec = await EmbeddingService.embed("cached_text")
        assert vec == [0.5] * 384

    @pytest.mark.asyncio
    async def test_embed_song_builds_rich_text(self):
        from embeddings.embedding_service import EmbeddingService
        calls = []
        async def fake_embed(text):
            calls.append(text)
            return [0.0] * 384
        with patch.object(EmbeddingService, "embed", side_effect=fake_embed):
            await EmbeddingService.embed_song({
                "title": "Test", "artist": "Artist", "genre": "Rock",
                "energy_level": "high", "mood_tags": ["happy"],
                "context_tags": ["gym"], "lyrics_summary": "A great song."
            })
        assert len(calls) == 1
        assert "Test" in calls[0]
        assert "Rock" in calls[0]


# ─── Security Filter ───────────────────────────────────────────────────────────

class TestSecurityFilter:
    def test_blocks_banking(self):
        import re
        BLOCKED = [r"chase\.com", r"bankof", r"paypal\.com", r"stripe\.com"]
        def is_sensitive(h):
            return any(re.search(p, h) for p in BLOCKED)
        assert is_sensitive("www.chase.com")
        assert is_sensitive("bankofamerica.com")
        assert not is_sensitive("discord.com")
        assert not is_sensitive("web.whatsapp.com")

    def test_strips_otp(self):
        import re
        def sanitize(t):
            return re.sub(r'\b\d{4,8}\b', '[redacted]', t)
        assert "[redacted]" in sanitize("Your OTP is 847291")
        assert "847291" not in sanitize("Your OTP is 847291")

    def test_strips_credit_card(self):
        import re
        def sanitize(t):
            return re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[card]', t)
        assert "[card]" in sanitize("card: 4111 1111 1111 1111")


# ─── YouTube Service ───────────────────────────────────────────────────────────

class TestYouTubeService:
    def test_build_url_contains_song(self):
        from services.youtube_service import YouTubeService
        url = YouTubeService.build_url("Lose Yourself", "Eminem")
        assert "youtube.com/results" in url
        assert "Lose" in url

    def test_playlist_uses_emotion(self):
        from services.youtube_service import YouTubeService
        url = YouTubeService.build_playlist_url("motivated", "career")
        assert "youtube.com" in url

    def test_playlist_fallback_works(self):
        from services.youtube_service import YouTubeService
        url = YouTubeService.build_playlist_url("unknown", "unknown")
        assert "youtube.com" in url
