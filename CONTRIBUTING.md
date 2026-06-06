# Contributing to MoodTunes AI

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Project Structure

```
moodtunes-ai/
├── extension/          Chrome Extension (MV3, vanilla JS)
│   ├── background/     Service worker
│   ├── content/        Platform adapters + security filter
│   ├── popup/          Extension popup (plain JS + CSS)
│   ├── options/        Settings page
│   ├── notifications/  Chrome notification manager
│   └── storage/        chrome.storage wrapper
│
├── backend/            FastAPI Python backend
│   ├── api/routes/     HTTP endpoints
│   ├── services/       Emotion, context, intent, YouTube
│   ├── rag/            ChromaDB vector store + pipeline
│   ├── embeddings/     nomic-embed-text via Ollama
│   ├── recommendations/Hybrid scoring engine
│   ├── memory/         User preference memory
│   ├── repositories/   DB abstraction layer
│   ├── models/         Pydantic schemas
│   ├── database/       SQLite init + async wrapper
│   └── tests/          Unit, integration, E2E
│
├── scripts/            Dataset generation + tooling
├── docs/               Architecture + sequence diagrams
└── docker-compose.yml  One-command stack startup
```

## Development Workflow

### 1. Set up environment

```bash
git clone https://github.com/yourname/moodtunes-ai
cd moodtunes-ai
make up          # Start Docker stack
make ingest      # Populate song database
make health      # Verify everything is running
```

### 2. Backend development

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### 3. Run tests before submitting

```bash
make test        # Unit + integration
make coverage    # Must be 80%+
```

## Adding a New Platform Adapter

1. Create `extension/content/adapters/myplatform-adapter.js`:

```javascript
export class MyPlatformAdapter {
  observe(callback) {
    const observer = new MutationObserver(() => {
      const text = this._extractText();
      if (text) callback(text);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  _extractText() {
    const msgs = document.querySelectorAll('.your-message-selector');
    return [...msgs].slice(-20).map(m => m.innerText).join('\n');
  }

  disconnect() {}
}
```

2. Register it in `extension/content/content-main.js`:

```javascript
import { MyPlatformAdapter } from './adapters/myplatform-adapter.js';

const PLATFORM_MAP = [
  // ... existing entries ...
  { match: /myplatform\.com/, Adapter: MyPlatformAdapter, source: 'myplatform' },
];
```

## Adding a New Emotion or Context

### New Emotion

1. Add to `EMOTION_TO_MOOD` in `backend/recommendations/recommendation_engine.py`
2. Add to the prompt in `backend/services/emotion_service.py`
3. Add emoji to `EMOTION_EMOJI` in both `extension/background/service-worker.js` and `extension/popup/popup.js`

### New Context

1. Add to `CONTEXT_PLAYLIST_QUERIES` in `backend/services/youtube_service.py`
2. Add to the prompt in `backend/services/context_service.py`

## Coding Standards

### Python

- Follow PEP 8
- Use type hints everywhere
- Keep functions under 40 lines
- Use `async/await` for all I/O
- Write tests for every new service method

### JavaScript

- Use ES modules (`import`/`export`)
- No external JS dependencies in the extension
- Always handle `chrome.runtime.sendMessage` errors
- Security: never log conversation text to console

## Pull Request Checklist

- [ ] Tests written and passing (`make test`)
- [ ] Coverage does not drop below 80% (`make coverage`)
- [ ] No sensitive data logged to console
- [ ] Security filter updated if new input types added
- [ ] README updated if new feature added
- [ ] Docker build still works (`docker build ./backend`)

## Reporting Issues

Please include:
- Chrome version
- Extension version
- Backend health check output (`make health`)
- Steps to reproduce
- Expected vs actual behaviour

## License

By contributing, you agree your contributions will be licensed under the MIT License.
