#!/usr/bin/env bash
# MoodTunes AI – One-shot local setup (no Docker)
set -e

echo "🎵 MoodTunes AI Setup"
echo "====================="

# 1. Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3.10+ required. Install from https://python.org"
  exit 1
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PY_VER found"

# 2. Install dependencies
echo ""
echo "Installing Python packages..."
pip install -r backend/requirements.txt -q
echo "✅ Packages installed"

# 3. Create .env if missing
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo ""
  echo "⚠️  Created backend/.env from template."
  echo "    → Open backend/.env and set your GROQ_API_KEY"
  echo "    → Get a FREE key at: https://console.groq.com"
else
  echo "✅ backend/.env already exists"
fi

# 4. Create data directory
mkdir -p backend/data
echo "✅ data/ directory ready"

echo ""
echo "🚀 Setup complete! Next steps:"
echo ""
echo "  Terminal 1 — Start backend:"
echo "    cd backend && uvicorn app:app --reload"
echo ""
echo "  Terminal 2 — Load song database (run once):"
echo "    cd backend && python ../scripts/generate_dataset.py"
echo ""
echo "  Chrome — Load extension:"
echo "    chrome://extensions/ → Developer Mode → Load Unpacked → ./extension/"
echo ""
echo "  Verify health:"
echo "    curl http://localhost:8000/api/v1/health"
