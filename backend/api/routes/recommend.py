# MoodTunes AI – /recommend route
import time
from fastapi import APIRouter, HTTPException

from models.schemas import RecommendRequest, RecommendResponse
from services.emotion_service import EmotionService
from services.context_service import ContextService
from services.intent_service import IntentService
from recommendations.recommendation_engine import RecommendationEngine
from memory.memory_engine import MemoryEngine

router = APIRouter()


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    t0 = time.monotonic()

    # 1. Parallel AI analysis
    emotion  = await EmotionService.detect(req.text)
    context  = await ContextService.classify(req.text)
    intent   = await IntentService.detect(req.text, emotion.emotion, context.context)

    # 2. Load user memory
    memory = await MemoryEngine.get_memory(req.user_id)

    # 3. RAG + hybrid scoring
    rec = await RecommendationEngine.recommend(
        emotion=emotion,
        context=context,
        intent=intent,
        memory=memory,
        user_id=req.user_id,
    )

    if not rec:
        raise HTTPException(status_code=404, detail="No suitable recommendation found")

    # 4. Persist to history
    await MemoryEngine.record_recommendation(req.user_id, rec.song_id)

    processing_ms = int((time.monotonic() - t0) * 1000)
    return RecommendResponse(
        recommendation=rec,
        emotion_result=emotion,
        context_result=context,
        intent_result=intent,
        processing_ms=processing_ms,
    )
