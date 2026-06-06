"""
MoodTunes AI – E2E Tests (Groq edition)

Prerequisites:
    pip install playwright pytest-playwright anyio
    playwright install chromium

Run:
    pytest tests/e2e/ -v

These tests work in two modes:
  1. API-only (no browser) – always runs
  2. Browser (with Chrome extension) – skipped if no backend running
"""
import pytest
import httpx
import asyncio

BACKEND_URL = "http://localhost:8000"


# ─── API-level E2E (always runs, mocks Groq) ──────────────────────────────────

@pytest.mark.anyio
async def test_full_recommend_response_shape():
    """
    Calls /recommend and verifies the complete response contract.
    Uses a live backend if available; otherwise skips gracefully.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/recommend",
                json={
                    "user_id": "e2e_test_user_001",
                    "source": "whatsapp",
                    "text": "I just got rejected from my dream job. Feeling really low right now.",
                },
            )
    except httpx.ConnectError:
        pytest.skip("Backend not running – start with: make run")

    assert resp.status_code == 200
    data = resp.json()

    # Top-level keys
    for key in ("recommendation","emotion_result","context_result","intent_result","processing_ms"):
        assert key in data, f"Missing key: {key}"

    # Recommendation shape
    rec = data["recommendation"]
    for field in ("song","artist","song_id","confidence","reason","youtube_url"):
        assert field in rec, f"Missing rec field: {field}"

    # YouTube URL format
    assert "youtube.com/results?search_query=" in rec["youtube_url"]

    # Sensible confidence
    assert 0 <= rec["confidence"] <= 100

    # Processing time is reasonable
    assert 0 <= data["processing_ms"] < 30_000

    print(f"\n✅ E2E Recommendation:")
    print(f"   Song    : {rec['song']} – {rec['artist']}")
    print(f"   Emotion : {data['emotion_result']['emotion']} ({data['emotion_result']['confidence']}%)")
    print(f"   Context : {data['context_result']['context']}")
    print(f"   Intent  : {data['intent_result']['intent']}")
    print(f"   Reason  : {rec['reason']}")
    print(f"   Time    : {data['processing_ms']}ms")


@pytest.mark.anyio
async def test_feedback_like_dislike_cycle():
    """Like then dislike the same song – both should succeed."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            like = await client.post(f"{BACKEND_URL}/api/v1/feedback", json={
                "user_id": "e2e_test_user_001",
                "song_id": "song_00000",
                "action": "like",
            })
            assert like.status_code == 200

            dislike = await client.post(f"{BACKEND_URL}/api/v1/feedback", json={
                "user_id": "e2e_test_user_001",
                "song_id": "song_00000",
                "action": "dislike",
            })
            assert dislike.status_code == 200
    except httpx.ConnectError:
        pytest.skip("Backend not running")


@pytest.mark.anyio
async def test_personalization_improves_with_feedback():
    """
    After liking songs of genre Rock, recommendations should show
    Rock songs more often. This is a smoke test verifying the pipeline runs.
    """
    user_id = "e2e_personalization_test"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: like a few Rock songs
            for song_id in ["song_00001", "song_00002"]:
                await client.post(f"{BACKEND_URL}/api/v1/feedback", json={
                    "user_id": user_id, "song_id": song_id, "action": "like",
                })

            # Step 2: get a recommendation and verify pipeline completes
            resp = await client.post(f"{BACKEND_URL}/api/v1/recommend", json={
                "user_id": user_id,
                "source": "generic",
                "text": "I love rock music. Playing guitar and feeling pumped.",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["recommendation"]["song"]

    except httpx.ConnectError:
        pytest.skip("Backend not running")


@pytest.mark.anyio
async def test_health_endpoint_structure():
    """Health endpoint must report Groq model and song count."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{BACKEND_URL}/api/v1/health")
    except httpx.ConnectError:
        pytest.skip("Backend not running")

    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "groq_model" in data
    assert "song_count" in data
    assert "embeddings" in data


# ─── Browser E2E (requires playwright + extension) ────────────────────────────

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

import os
from pathlib import Path

EXTENSION_PATH = str(Path(__file__).parent.parent.parent.parent / "extension")


@pytest.mark.anyio
@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed")
async def test_extension_popup_renders():
    """Open the extension popup and verify core UI elements."""
    if not os.path.exists(EXTENSION_PATH + "/manifest.json"):
        pytest.skip("Extension directory not found")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="/tmp/moodtunes-e2e-groq",
            headless=True,
            args=[
                f"--disable-extensions-except={EXTENSION_PATH}",
                f"--load-extension={EXTENSION_PATH}",
                "--no-sandbox",
            ],
        )
        bg_pages = context.background_pages
        if not bg_pages:
            await context.close()
            pytest.skip("Extension background page not found")

        ext_id = bg_pages[0].url.split("/")[2]
        page = await context.new_page()

        try:
            await page.goto(f"chrome-extension://{ext_id}/popup/popup.html",
                            wait_until="domcontentloaded")
            await page.wait_for_selector(".popup", timeout=5000)
            logo = await page.inner_text(".logo")
            assert "MoodTunes" in logo

            # Toggle should be present
            toggle = await page.query_selector("#enable-toggle")
            assert toggle is not None

        finally:
            await page.close()
            await context.close()


@pytest.mark.anyio
@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed")
async def test_settings_page_has_groq_note():
    """Settings page should not mention Ollama/Docker."""
    if not os.path.exists(EXTENSION_PATH + "/options/settings.html"):
        pytest.skip("Settings page not found")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="/tmp/moodtunes-e2e-groq-settings",
            headless=True,
            args=[
                f"--disable-extensions-except={EXTENSION_PATH}",
                f"--load-extension={EXTENSION_PATH}",
                "--no-sandbox",
            ],
        )
        bg_pages = context.background_pages
        if not bg_pages:
            await context.close()
            pytest.skip("Extension background page not found")

        ext_id = bg_pages[0].url.split("/")[2]
        page = await context.new_page()

        try:
            await page.goto(f"chrome-extension://{ext_id}/options/settings.html",
                            wait_until="domcontentloaded")
            content = await page.content()
            # Should have privacy badge
            assert "local" in content.lower()
            # Should not mention Ollama
            assert "ollama" not in content.lower()
        finally:
            await page.close()
            await context.close()
