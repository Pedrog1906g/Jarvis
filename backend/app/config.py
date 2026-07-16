import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM Providers ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # groq | openai | ollama | anthropic | google

# --- Groq ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3")

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# --- Ollama ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# --- Anthropic (Claude) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# --- Google (Gemini) ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-exp")

# --- Determine DEMO_MODE ---
# Check if any provider is configured
has_groq = bool(GROQ_API_KEY)
has_openai = bool(OPENAI_API_KEY)
has_ollama = True  # Assume Ollama is available locally if used
has_anthropic = bool(ANTHROPIC_API_KEY)
has_google = bool(GOOGLE_API_KEY)

DEMO_MODE = not (has_groq or has_openai or has_anthropic or has_google)

# --- Segurança ---
JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SESSION_SECRET", "nexus-jarvis-secret-2024")
JWT_ALGORITHM = "HS256"
OWNER_PASSPHRASE = os.getenv("OWNER_PASSPHRASE", "nexus")
TOKEN_EXPIRE_HOURS = 24 * 30  # 30 dias

# --- Banco ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nexus.db")

# --- Voz / TTS ---
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "android")  # android | openai | piper
OPENAI_TTS_API_KEY = os.getenv("OPENAI_TTS_API_KEY", "")

# Piper TTS offline (https://github.com/rhasspy/piper)
# Modelo recomendado para PT-BR: pt_BR-faber-medium (baixar de https://huggingface.co/rhasspy/piper-voices)
PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "")
PIPER_EXECUTABLE = os.getenv("PIPER_EXECUTABLE", "piper")  # caminho para o binário piper

# Spotify OAuth2 (https://developer.spotify.com/dashboard)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "")

# --- Rede ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# --- Firebase (opcional, via variáveis de ambiente no Render) ---
# Se definidas, o backend inicializa o Firebase Admin SDK e espelha dados no Firestore.
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL", "")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "")
AUTH_MODE = os.getenv("AUTH_MODE", "jwt")  # jwt | firebase

# Auto-melhoria (somente o dono pode empurrar mudanças pro repo).
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Pedrog1906g/Jarvis")

APP_VERSION = "1.0.0"
APP_NAME = "NEXUS AI"
