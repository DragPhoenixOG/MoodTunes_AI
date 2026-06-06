# MoodTunes AI – Pydantic Models
from typing import Optional
from pydantic import BaseModel, Field


# ─── Request models ──────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    user_id: str
    source: str = "generic"
    text: str = Field(..., min_length=1, max_length=3000)


class FeedbackRequest(BaseModel):
    user_id: str
    song_id: str
    action: str  # play | playlist | like | dislike | skip | snooze


# ─── AI result models ─────────────────────────────────────────────────────────

class EmotionResult(BaseModel):
    emotion: str
    confidence: int
    reason: str


class ContextResult(BaseModel):
    context: str
    confidence: int


class IntentResult(BaseModel):
    intent: str


# ─── Song model ───────────────────────────────────────────────────────────────

class SongSchema(BaseModel):
    song_id: str
    title: str
    artist: str
    genre: str
    energy_level: str          # low | medium | high
    mood_tags: list[str]
    context_tags: list[str]
    lyrics_summary: str
    youtube_url: str
    playlist_url: Optional[str] = None


# ─── Recommendation output ────────────────────────────────────────────────────

class RecommendationOutput(BaseModel):
    song: str
    artist: str
    song_id: str
    confidence: int
    reason: str
    youtube_url: str
    playlist_url: Optional[str] = None


class RecommendResponse(BaseModel):
    recommendation: RecommendationOutput
    emotion_result: EmotionResult
    context_result: ContextResult
    intent_result: IntentResult
    processing_ms: int


# ─── User memory ──────────────────────────────────────────────────────────────

class UserMemory(BaseModel):
    user_id: str
    liked_songs: list[str] = []
    disliked_songs: list[str] = []
    favorite_artists: list[str] = []
    favorite_genres: list[str] = []
    recent_recommendations: list[str] = []
    preferred_genres: list[str] = []
