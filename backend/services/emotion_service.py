# MoodTunes AI – Emotion Detection via Groq API
import json
from groq import AsyncGroq
from config import GROQ_API_KEY, GROQ_MODEL
from models.schemas import EmotionResult

EMOTIONS = [
    "happy", "sad", "motivated", "excited", "confident", "anxious",
    "focused", "burned_out", "romantic", "heartbroken", "relaxed",
    "angry", "celebratory", "productive", "workout"
]

SYSTEM_PROMPT = (
    "You are an emotion detection system. Respond ONLY with a JSON object, "
    "no markdown, no extra text."
)

USER_PROMPT = """Analyse the following conversation text and identify the dominant emotion.

SUPPORTED EMOTIONS: {emotions}

TEXT:
{text}

Respond with exactly this JSON structure:
{{"emotion": "<one emotion from the list>", "confidence": <0-100>, "reason": "<one sentence>"}}"""


class EmotionService:
    _client: AsyncGroq | None = None

    @classmethod
    def _get_client(cls) -> AsyncGroq:
        if cls._client is None:
            cls._client = AsyncGroq(api_key=GROQ_API_KEY)
        return cls._client

    @classmethod
    async def detect(cls, text: str) -> EmotionResult:
        try:
            client = cls._get_client()
            response = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT.format(
                        emotions=", ".join(EMOTIONS),
                        text=text[:1500]
                    )},
                ],
                temperature=0.2,
                max_tokens=150,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)
            emotion = data.get("emotion", "relaxed").lower().replace(" ", "_")
            # Validate against known list
            if emotion not in EMOTIONS:
                emotion = "relaxed"
            return EmotionResult(
                emotion=emotion,
                confidence=int(data.get("confidence", 70)),
                reason=data.get("reason", ""),
            )
        except Exception as e:
            return EmotionResult(emotion="relaxed", confidence=50,
                                 reason=f"Detection unavailable: {e}")
