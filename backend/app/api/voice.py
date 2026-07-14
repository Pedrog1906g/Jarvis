from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.core.voice import transcribe_audio, synthesize_speech

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...), db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    data = await file.read()
    text = transcribe_audio(data, file.filename or "audio.webm")
    return {"text": text}


@router.post("/synthesize")
async def synthesize(body: dict, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    text = body.get("text", "")
    audio = synthesize_speech(text)
    if audio is None:
        return Response(status_code=204)
    return Response(content=audio, media_type="audio/mpeg")
