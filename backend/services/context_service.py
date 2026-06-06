# MoodTunes AI – Context Classification & Intent Detection via Groq API
import json
from groq import AsyncGroq
from config import GROQ_API_KEY, GROQ_MODEL
from models.schemas import ContextResult, IntentResult

CONTEXTS = [
    "interview", "coding", "study", "gym", "workout", "startup",
    "career", "relationship", "breakup", "gaming", "travel",
    "celebration", "business", "learning", "stress"
]

INTENTS = [
    "Need Motivation", "Need Focus", "Need Confidence", "Need Relaxation",
    "Need Energy", "Need Comfort", "Need Recovery", "Need Inspiration", "Need Celebration"
]

SYSTEM_PROMPT = "You are a classification system. Respond ONLY with valid JSON, no markdown."

CONTEXT_PROMPT = """Classify the life/work context of the following text.

SUPPORTED CONTEXTS: {contexts}

TEXT: {text}

JSON response: {{"context": "<one context>", "confidence": <0-100>}}"""

INTENT_PROMPT = """Given this person's situation, what kind of music support do they need?

EMOTION: {emotion}
CONTEXT: {context}
TEXT: {text}

SUPPORTED INTENTS: {intents}

JSON response: {{"intent": "<one intent>"}}"""


class ContextService:
    _client: AsyncGroq | None = None

    @classmethod
    def _get_client(cls) -> AsyncGroq:
        if cls._client is None:
            cls._client = AsyncGroq(api_key=GROQ_API_KEY)
        return cls._client

    @classmethod
    async def classify(cls, text: str) -> ContextResult:
        try:
            client = cls._get_client()
            resp = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": CONTEXT_PROMPT.format(
                        contexts=", ".join(CONTEXTS), text=text[:1500]
                    )},
                ],
                temperature=0.1,
                max_tokens=80,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content)
            context = data.get("context", "general").lower()
            if context not in CONTEXTS:
                context = "general"
            return ContextResult(context=context,
                                 confidence=int(data.get("confidence", 70)))
        except Exception:
            return ContextResult(context="general", confidence=50)


class IntentService:
    _client: AsyncGroq | None = None

    @classmethod
    def _get_client(cls) -> AsyncGroq:
        if cls._client is None:
            cls._client = AsyncGroq(api_key=GROQ_API_KEY)
        return cls._client

    @classmethod
    async def detect(cls, text: str, emotion: str, context: str) -> IntentResult:
        try:
            client = cls._get_client()
            resp = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": INTENT_PROMPT.format(
                        emotion=emotion, context=context,
                        text=text[:1000], intents=", ".join(INTENTS)
                    )},
                ],
                temperature=0.1,
                max_tokens=60,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content)
            intent = data.get("intent", "Need Relaxation")
            if intent not in INTENTS:
                intent = "Need Relaxation"
            return IntentResult(intent=intent)
        except Exception:
            return IntentResult(intent="Need Relaxation")
