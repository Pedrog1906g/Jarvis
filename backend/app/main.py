import os

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.db import models  # registra os modelos
from app.api import auth, chat, voice, reminders, plugins, system, agent, scheduled_tasks, obsidian, metrics
from app.services.reminder_scheduler import start_scheduler
from app.services.scheduled_tasks import start_scheduled_tasks
from app.services.learning_loop import start_learning_loop
from app.core.discovery import start_discovery
from app.core.firebase import init_firebase
from app.config import APP_NAME, APP_VERSION

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    start_scheduled_tasks()  # executa tarefas agendadas (ex.: auto-melhoria de 20 em 20 dias)
    start_learning_loop()  # gera aprendizados periodicos (loop de ensino continuo do NEXUS)
    start_discovery()  # anuncia o backend na LAN via mDNS (auto-descoberta no app)
    init_firebase()    # inicializa Firebase Admin se as env vars estiverem presentes
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(voice.router)
app.include_router(reminders.router)
app.include_router(plugins.router)
app.include_router(system.router)
app.include_router(agent.router)
app.include_router(scheduled_tasks.router)
app.include_router(obsidian.router)
app.include_router(metrics.router)


# Diretório do frontend web (HUD do JARVIS para PC).
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "web"))


@app.get("/web")
def web_app():
    """HUD do JARVIS (frontend web para PC/desktop)."""
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


@app.get("/")
def root():
    """Na raiz, abre o HUD do JARVIS no navegador (uso no PC)."""
    return FileResponse(os.path.join(WEB_DIR, "index.html"))
