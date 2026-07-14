from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.security import hash_passphrase, create_token, ensure_owner

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = "owner"
    passphrase: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = ensure_owner(db)
    if user.username != req.username or user.passphrase_hash != hash_passphrase(req.passphrase):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_token(user.id, user.username)
    return TokenResponse(
        access_token=token,
        user={"id": user.id, "username": user.username, "display_name": user.display_name},
    )


@router.get("/me")
def me(current=Depends(lambda: None)):
    # placeholder; o app usa /api/system/info após login
    return {"ok": True}
