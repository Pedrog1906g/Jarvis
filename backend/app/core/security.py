from datetime import datetime, timedelta, timezone
import hashlib
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import JWT_SECRET, JWT_ALGORITHM, TOKEN_EXPIRE_HOURS, OWNER_PASSPHRASE
from app.db.database import get_db
from app.db import models

bearer_scheme = HTTPBearer(auto_error=False)


def hash_passphrase(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()


def create_token(user_id: int, username: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "username": username, "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def ensure_owner(db: Session) -> models.User:
    user = db.query(models.User).filter(models.User.username == "owner").first()
    if not user:
        user = models.User(
            username="owner",
            passphrase_hash=hash_passphrase(OWNER_PASSPHRASE),
            display_name="Owner",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
    try:
        payload = decode_token(creds.credentials)
        user = db.query(models.User).filter(models.User.id == int(payload["sub"])).first()
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    return user


def ws_user(token: str, db: Session) -> models.User:
    try:
        payload = decode_token(token)
        user = db.query(models.User).filter(models.User.id == int(payload["sub"])).first()
    except Exception:
        return None
    return user
