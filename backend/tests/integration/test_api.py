# MoodTunes AI – Integration Tests (Groq edition)
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock

from app import app
from models.schemas import (
    EmotionResult, ContextResult, IntentResult, RecommendationOutput, UserMemory
)

MOCK_REC = RecommendationOutput(
    song="Lose Yourself", artist="Eminem", song_id="song_00002",
    confidence=96, reason="High-energy motivational track for interview prep.",
    youtube_url="https://www.youtube.com/results?search_query=Lose+Yourself+Eminem+official",
)
MOCK_EMOTION = EmotionResult(emotion="motivated", confidence=92, reason="Determined tone.")
MOCK_CONTEXT = ContextResult(context="interview", confidence=95)
MOCK_INTENT  = IntentResult(intent="Need Confidence")
MOCK_MEMORY  = UserMemory(user_id="test123")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/")
    assert resp.status_code == 200
    assert "MoodTunes" in resp.json()["service"]


@pytest.mark.anyio
async def test_recommend_full_pipeline():
    with (
        patch("services.emotion_service.EmotionService.detect",
              new_callable=AsyncMock, return_value=MOCK_EMOTION),
        patch("services.context_service.ContextService.classify",
              new_callable=AsyncMock, return_value=MOCK_CONTEXT),
        patch("services.context_service.IntentService.detect",
              new_callable=AsyncMock, return_value=MOCK_INTENT),
        patch("memory.memory_engine.MemoryEngine.get_memory",
              new_callable=AsyncMock, return_value=MOCK_MEMORY),
        patch("recommendations.recommendation_engine.RecommendationEngine.recommend",
              new_callable=AsyncMock, return_value=MOCK_REC),
        patch("memory.memory_engine.MemoryEngine.record_recommendation",
              new_callable=AsyncMock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post("/api/v1/recommend", json={
                "user_id": "test123",
                "source": "whatsapp",
                "text": "Failed my interview today. Need to bounce back stronger.",
            })

    assert resp.status_code == 200
    data = resp.json()
    assert data["recommendation"]["song"] == "Lose Yourself"
    assert data["emotion_result"]["emotion"] == "motivated"
    assert data["context_result"]["context"] == "interview"
    assert data["intent_result"]["intent"] == "Need Confidence"
    assert data["processing_ms"] >= 0
    assert "youtube.com" in data["recommendation"]["youtube_url"]


@pytest.mark.anyio
async def test_recommend_validates_empty_text():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/api/v1/recommend", json={
            "user_id": "test123", "source": "whatsapp", "text": ""
        })
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_recommend_requires_user_id():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/api/v1/recommend", json={
            "source": "whatsapp", "text": "test text here"
        })
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_feedback_like():
    with patch("memory.memory_engine.MemoryEngine.record_feedback", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post("/api/v1/feedback", json={
                "user_id": "test123", "song_id": "song_00002", "action": "like"
            })
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.anyio
async def test_health_endpoint_returns_shape():
    with (
        patch("api.routes.health.AsyncGroq") as mock_groq,
        patch("api.routes.health.VectorStore.count", return_value=5247),
    ):
        mock_client = AsyncMock()
        mock_client.models.list = AsyncMock(return_value=[])
        mock_groq.return_value = mock_client

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/api/v1/health")

    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "groq_model" in data
    assert "song_count" in data
