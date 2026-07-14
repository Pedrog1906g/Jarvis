import os
from dotenv import load_dotenv

load_dotenv()

# --- Groq / LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3")

# Se não houver chave, roda em modo DEMO (respostas simuladas) para testar a UX.
DEMO_MODE = not bool(GROQ_API_KEY)

# --- Segurança ---
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
OWNER_PASSPHRASE = os.getenv("OWNER_PASSPHRASE", "nexus")
TOKEN_EXPIRE_HOURS = 24 * 30  # 30 dias

# --- Banco ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nexus.db")

# --- Voz / TTS ---
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "android")  # android | openai | piper
OPENAI_TTS_API_KEY = os.getenv("OPENAI_TTS_API_KEY", "")

# --- Rede ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# --- Firebase (opcional, via variáveis de ambiente no Render) ---
# Se definidas, o backend inicializa o Firebase Admin SDK e espelha dados no Firestore.
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL", "")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "")
AUTH_MODE = os.getenv("AUTH_MODE", "jwt")  # jwt | firebase

APP_VERSION = "1.0.0"
APP_NAME = "NEXUS AI"
