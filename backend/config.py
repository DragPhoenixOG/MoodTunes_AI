# MoodTunes AI – Centralised Configuration
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL     = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
EMBEDDING_MODEL= os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHROMA_PATH    = os.getenv("CHROMA_PATH", "./data/chromadb")
DB_PATH        = os.getenv("DB_PATH", "./data/moodtunes.db")
HOST           = os.getenv("HOST", "0.0.0.0")
PORT           = int(os.getenv("PORT", "8000"))

if not GROQ_API_KEY:
    print("⚠  WARNING: GROQ_API_KEY not set. Copy .env.example → .env and add your key.")
    print("   Get a free key at https://console.groq.com")
