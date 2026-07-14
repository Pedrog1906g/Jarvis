from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.db import models  # registra os modelos
from app.api import auth, chat, voice, reminders, plugins, system, agent, scheduled_tasks, obsidian
from app.services.reminder_scheduler import start_scheduler
from app.services.scheduled_tasks import start_scheduled_tasks
from app.core.discovery import start_discovery
from app.core.firebase import init_firebase
from app.config import APP_NAME, APP_VERSION

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    start_scheduled_tasks()  # executa tarefas agendadas (ex.: auto-melhoria de 20 em 20 dias)
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


@app.get("/")
def root():
    return {"name": APP_NAME, "status": "online", "version": APP_VERSION,
            "docs": "/docs"}
