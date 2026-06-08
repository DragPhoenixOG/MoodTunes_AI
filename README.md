# 🎵 MoodTunes AI

> Your AI-powered personal DJ. Monitors browser conversations, detects your mood with **Groq's ultra-fast LLM API**, and recommends music — no Docker, no Ollama, just `pip install` and go.

---

| Feature | Ollama Edition | **Groq Edition** |
|---|---|---|
| LLM inference | Local Ollama (8GB+ RAM) | **Groq API (free tier)** |
| Setup | Docker + model pull (~10 GB) | `pip install` only |
| Speed | ~2-5s per call | **~150ms per call** |
| Embeddings | nomic-embed-text (Ollama) | **sentence-transformers (local, CPU)** |
| Vector DB | ChromaDB (Docker server) | **ChromaDB (local file, no server)** |
| Privacy | 100% local | Conversations stay local; only emotion labels go to Groq |
| First run time | ~15 min (model download) | **~2 min** |

---

## Architecture

```
Chrome Extension (MV3)
  └── Content Scripts  – MutationObserver on 10 platforms
  └── Service Worker   – orchestrates context → API → notification
  └── Popup UI         – history + snooze controls
        │
        │ HTTP/JSON  (localhost only)
        ▼
FastAPI Backend  (localhost:8000)
  ├── Groq API ──────────────────────── llama-3.1-8b-instant (or 70B)
  │   ├── Emotion Detection             15 emotions, JSON mode
  │   ├── Context Classification        15 contexts
  │   └── Intent Detection              9 intents
  │
  ├── sentence-transformers ──────────── all-MiniLM-L6-v2 (local, CPU)
  │   └── Embedding Service             384-dim vectors, LRU cache
  │
  ├── ChromaDB (PersistentClient) ────── ./data/chromadb/  (no server)
  │   └── 5,000+ songs, cosine similarity
  │
  ├── Hybrid Scorer
  │   emotion 40% · context 25% · intent 15% · user history 20%
  │
  ├── Memory Engine ──────────────────── SQLite  ./data/moodtunes.db
  │   liked/disliked songs · genre scores · favourite artists
  │
  └── YouTube URL Builder ────────────── no API key, dynamic search URLs
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | [python.org](https://python.org) |
| Chrome 120+ | For the extension |
| Groq API key | Free at [console.groq.com](https://console.groq.com) |
| ~500 MB disk | For embedding model + song DB |
| 4 GB RAM | Minimum (embedding model runs on CPU) |

> **No Docker. No Ollama. No GPU required.**

---

## Quick Start (5 minutes)

### 1. Clone and install

```bash
git clone https://github.com/DragPhoenixOG/MoodTunes_AI
cd MoodTunes_AI

# Install all Python dependencies
pip install -r backend/requirements.txt
# This downloads: fastapi, groq, sentence-transformers, chromadb, etc.
```

### 2. Configure your Groq API key

```bash
cp backend/.env.example backend/.env
# Edit backend/.env:
#   GROQ_API_KEY=gsk_your_key_here
```

Get a **free** API key at [console.groq.com](https://console.groq.com) — no credit card needed.

### 3. Start the backend

```bash
cd backend
uvicorn app:app --reload --port 8000
```

First run downloads the embedding model (~90 MB). You'll see:

```
[Embeddings] Loading all-MiniLM-L6-v2...
[Embeddings] Model ready. Dimension: 384
[ChromaDB] Connected. Songs in DB: 0
[MoodTunes] Ready at http://localhost:8000
```

### 4. Ingest the song database (run once)

In a second terminal:

```bash
cd backend
python ../scripts/generate_dataset.py
# → Generates 5,000+ songs and embeds them locally
# → Takes ~3-5 minutes (embedding 5k songs)
```

### 5. Install the Chrome extension

1. Open **`chrome://extensions/`**
2. Enable **Developer Mode** (top-right toggle)
3. Click **Load unpacked**
4. Select the **`extension/`** folder
5. Pin the MoodTunes AI extension 📌

### 6. Verify

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "ok",
  "groq_api": true,
  "groq_model": "llama-3.1-8b-instant",
  "chromadb": "local",
  "song_count": 5247,
  "embeddings": "sentence-transformers (local)"
}
```

Open WhatsApp Web, have a conversation, wait ~60 seconds → 🎵 notification appears.

---

## Available Groq Models

Set `GROQ_MODEL` in `backend/.env` or change it in the extension settings:

| Model | Speed | Quality | Notes |
|---|---|---|---|
| `llama-3.1-8b-instant` | ⚡ ~100ms | ★★★★ | **Default. Best for most users.** |
| `llama-3.3-70b-versatile` | ~400ms | ★★★★★ | More nuanced emotion detection |
| `mixtral-8x7b-32768` | ~200ms | ★★★★ | Good balance |
| `gemma2-9b-it` | ~200ms | ★★★★ | Google model |

---

## How It Works

### 1. Content Detection
The extension uses `MutationObserver` on 10 supported platforms. Text is:
- Debounced (3 seconds) to avoid per-keystroke calls
- Sanitised (OTPs, credit cards, JWTs stripped)
- Capped at 2,000 characters

### 2. Groq AI Analysis (parallel, ~150ms)
Three simultaneous Groq calls with `json_object` response mode:
```
Emotion: "Bro I failed my interview today"  →  sad (94%)
Context:                                    →  interview (97%)
Intent:                                     →  Need Motivation
```

### 3. RAG Retrieval
The query is embedded locally using `all-MiniLM-L6-v2`, then searched against 5,000+ songs in ChromaDB with cosine similarity. Top 20 candidates are retrieved.

### 4. Hybrid Scoring
```
Final Score = emotion_match × 0.40
            + context_match × 0.25
            + intent_match  × 0.15
            + user_history  × 0.20
            + (1 - cosine_distance) × 0.05
```

### 5. Personalisation
After you like/dislike/play songs, the Memory Engine updates your genre scores in SQLite. Next recommendations automatically favour your preferred genres and artists.

---

## Project Structure

```
moodtunes-ai/
├── backend/
│   ├── app.py                        FastAPI entry point
│   ├── config.py                     Centralised .env config
│   ├── .env.example                  Template (copy to .env)
│   ├── requirements.txt              pip dependencies only
│   │
│   ├── api/routes/
│   │   ├── recommend.py              POST /api/v1/recommend
│   │   ├── feedback.py               POST /api/v1/feedback
│   │   ├── health.py                 GET  /api/v1/health
│   │   └── songs.py                  POST /api/v1/songs/ingest
│   │
│   ├── services/
│   │   ├── emotion_service.py        Groq → 15 emotions
│   │   ├── context_service.py        Groq → 15 contexts + 9 intents
│   │   └── youtube_service.py        Dynamic YouTube URLs
│   │
│   ├── embeddings/
│   │   └── embedding_service.py      sentence-transformers (local)
│   │
│   ├── rag/
│   │   ├── vector_store.py           ChromaDB PersistentClient
│   │   └── rag_pipeline.py           Retrieve → filter → re-rank
│   │
│   ├── recommendations/
│   │   └── recommendation_engine.py  Hybrid scorer
│   │
│   ├── memory/
│   │   └── memory_engine.py          SQLite user profiles
│   │
│   ├── repositories/
│   │   ├── song_repository.py        Song CRUD
│   │   └── user_repository.py        User CRUD
│   │
│   ├── database/
│   │   └── db.py                     SQLite schema + async wrapper
│   │
│   └── tests/
│       ├── unit/                     Mocked unit tests
│       ├── integration/              FastAPI TestClient tests
│       └── e2e/                      Playwright + API tests
│
├── extension/
│   ├── manifest.json                 MV3
│   ├── background/service-worker.js  Orchestrator
│   ├── content/
│   │   ├── content-main.js           Platform detector
│   │   ├── security-filter.js        OTP/card/token scrubber
│   │   └── adapters/                 WhatsApp, Telegram, Discord...
│   ├── popup/                        History + snooze UI
│   ├── options/settings.html         Settings with Groq model picker
│   ├── notifications/                Chrome notification manager
│   └── storage/storage-service.js    chrome.storage wrapper
│
├── scripts/
│   ├── generate_dataset.py           5,000+ song generator + ingest
│   └── setup.sh                      One-shot setup script
│
├── docs/
│   └── sequence-diagram.mmd          Mermaid sequence diagram
│
├── Makefile                          make setup / run / test / ingest
└── README.md
```

---

## API Reference

Full interactive docs: **http://localhost:8000/docs**

### `POST /api/v1/recommend`

```json
// Request
{
  "user_id": "user_abc123",
  "source": "whatsapp",
  "text": "Bro I failed my interview today."
}

// Response
{
  "recommendation": {
    "song": "Hall Of Fame",
    "artist": "The Script",
    "song_id": "song_00000",
    "confidence": 96,
    "reason": "Hall Of Fame by The Script: suits sad feelings, aligns with interview situation, and helps you need motivation.",
    "youtube_url": "https://www.youtube.com/results?search_query=Hall+Of+Fame+The+Script+official"
  },
  "emotion_result":  { "emotion": "sad",       "confidence": 94, "reason": "..." },
  "context_result":  { "context": "interview",  "confidence": 97 },
  "intent_result":   { "intent": "Need Motivation" },
  "processing_ms":   187
}
```

### `POST /api/v1/feedback`

```json
{ "user_id": "...", "song_id": "song_00000", "action": "like" }
// action: play | playlist | like | dislike | skip | snooze
```

### `GET /api/v1/health`

```json
{
  "status": "ok",
  "groq_api": true,
  "groq_model": "llama-3.1-8b-instant",
  "chromadb": "local",
  "song_count": 5247,
  "embeddings": "sentence-transformers (local)"
}
```

---

## Testing

```bash
# All tests
make test

# Unit tests only (fast, no backend needed)
make test-unit

# Integration tests
make test-integration

# Coverage (target: 80%+)
make coverage

# E2E (requires running backend)
make test-e2e
```

---

## Troubleshooting

### `GROQ_API_KEY not set`
Copy `.env.example` → `.env` and add your key from [console.groq.com](https://console.groq.com).

### `song_count: 0` in health check
Run `make ingest` (or `python ../scripts/generate_dataset.py` from `backend/`).

### Extension not receiving notifications
- Check the backend is running: `make health`
- Check Chrome notifications are allowed for the extension
- Check the popup — is the toggle enabled?
- Look at service worker logs: `chrome://extensions/` → MoodTunes AI → Service Worker → Inspect

### Embedding model download is slow
It downloads `~90 MB` once on first startup. Subsequent starts are instant (cached in `~/.cache/huggingface/`).

### `chromadb` import error
```bash
pip install chromadb==0.5.15
```

---

## Privacy

| Data | Where it goes |
|---|---|
| Your conversation text | ❌ Never sent anywhere — stays in browser |
| Detected emotion label | ✅ Sent to Groq API (e.g. "sad") |
| Song preferences | ✅ Stored locally in SQLite |
| Embeddings | ✅ Generated locally on your CPU |

Groq's API processes the text you type **after** it's been summarised into an emotion label by the local content script. Your actual messages are never transmitted.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add platform adapters, new emotions, or new contexts.

```bash
# Adding a new platform adapter:
# 1. Create extension/content/adapters/myplatform-adapter.js
# 2. Register in extension/content/content-main.js PLATFORM_MAP
# 3. Add tests in backend/tests/unit/
# 4. Submit PR
```

## License

MIT
