from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.security import hash_passphrase, create_token, ensure_owner
from app.core.firebase import init_firebase, is_enabled, verify_id_token, mirror_user

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
    mirror_user(user)  # espelha no Firestore quando o Firebase está ativo
    return TokenResponse(
        access_token=token,
        user={"id": user.id, "username": user.username, "display_name": user.display_name},
    )


class FirebaseLoginRequest(BaseModel):
    id_token: str


@router.post("/firebase", response_model=TokenResponse)
def firebase_login(req: FirebaseLoginRequest, db: Session = Depends(get_db)):
    """Recebe um ID token do Firebase Auth, valida e emite o JWT do app (ponte Firebase → app)."""
    if not is_enabled():
        raise HTTPException(status_code=503, detail="Firebase não configurado no backend")
    try:
        decoded = verify_id_token(req.id_token)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=f"Token Firebase inválido: {e}")
    uid = decoded.get("uid") or decoded.get("sub")
    email = decoded.get("email", "")
    if not uid:
        raise HTTPException(status_code=401, detail="Token Firebase sem uid")
    user = db.query(models.User).filter(models.User.username == uid).first()
    if not user:
        user = models.User(username=uid, passphrase_hash="", display_name=email or uid)
        db.add(user)
        db.commit()
        db.refresh(user)
    mirror_user(user)
    token = create_token(user.id, user.username)
    return TokenResponse(
        access_token=token,
        user={"id": user.id, "username": user.username, "display_name": user.display_name},
    )


@router.get("/me")
def me(current=Depends(lambda: None)):
    # placeholder; o app usa /api/system/info após login
    return {"ok": True}
