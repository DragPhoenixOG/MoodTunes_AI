# MoodTunes AI – Makefile (Groq edition, no Docker)
.PHONY: setup run ingest test test-unit test-integration coverage health clean

# ── Setup ─────────────────────────────────────────────────────────────────────

setup:
	@echo "Installing Python dependencies..."
	pip install -r backend/requirements.txt
	@echo ""
	@echo "✅ Done! Next steps:"
	@echo "   1. cp backend/.env.example backend/.env"
	@echo "   2. Add your GROQ_API_KEY to backend/.env"
	@echo "      Get a free key at: https://console.groq.com"
	@echo "   3. make run"
	@echo "   4. make ingest   (in a second terminal)"

# ── Run ───────────────────────────────────────────────────────────────────────

run:
	@echo "Starting MoodTunes AI backend..."
	cd backend && uvicorn app:app --host 0.0.0.0 --port 8000 --reload

run-prod:
	cd backend && uvicorn app:app --host 0.0.0.0 --port 8000 --workers 2

# ── Dataset ───────────────────────────────────────────────────────────────────

ingest:
	@echo "Generating and ingesting 5,000+ song dataset..."
	cd backend && python ../scripts/generate_dataset.py

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	cd backend && pytest tests/unit tests/integration -v --tb=short

test-unit:
	cd backend && pytest tests/unit -v

test-integration:
	cd backend && pytest tests/integration -v

test-e2e:
	cd backend && pytest tests/e2e -v

coverage:
	cd backend && coverage run -m pytest tests/unit tests/integration
	cd backend && coverage report -m --fail-under=80

# ── Health ────────────────────────────────────────────────────────────────────

health:
	@curl -sf http://localhost:8000/api/v1/health | python3 -m json.tool \
	  || echo "❌ Backend not running. Try: make run"

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	rm -rf backend/data/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned data/ and __pycache__"

clean-embeddings:
	@echo "Clearing embedding cache only..."
	rm -rf backend/data/chromadb/

# ── Extension ─────────────────────────────────────────────────────────────────

ext-open:
	@echo "Load extension in Chrome:"
	@echo "  1. Open chrome://extensions/"
	@echo "  2. Enable Developer Mode"
	@echo "  3. Load Unpacked → select: $(PWD)/extension/"
