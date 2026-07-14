from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.db import models  # registra os modelos
from app.api import auth, chat, voice, reminders, plugins, system
from app.services.reminder_scheduler import start_scheduler
from app.config import APP_NAME, APP_VERSION

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
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


@app.get("/")
def root():
    return {"name": APP_NAME, "status": "online", "version": APP_VERSION,
            "docs": "/docs"}
