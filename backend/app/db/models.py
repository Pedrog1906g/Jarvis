from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    # Em produção use hash forte (bcrypt). Aqui usamos frase de acesso simples p/ testes.
    passphrase_hash = Column(String(255), nullable=False)
    display_name = Column(String(120), default="Owner")
    voiceprint = Column(Text, nullable=True)  # futuro: identificação por voz
    created_at = Column(DateTime, default=utcnow)

    conversations = relationship("Conversation", back_populates="owner")
    reminders = relationship("Reminder", back_populates="owner")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), default="Nova conversa")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class MemoryFact(Base):
    """Memória de longo prazo: fatos duráveis sobre o usuário/preferências."""
    __tablename__ = "memory_facts"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fact = Column(Text, nullable=False)
    category = Column(String(60), default="geral")  # comida, rotina, trabalho, etc.
    importance = Column(Integer, default=1)
    created_at = Column(DateTime, default=utcnow)

    owner = relationship("User")


class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    note = Column(Text, nullable=True)
    due_at = Column(DateTime, nullable=False)
    done = Column(Boolean, default=False)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    owner = relationship("User", back_populates="reminders")


class PluginState(Base):
    __tablename__ = "plugin_states"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False)
    enabled = Column(Boolean, default=False)
    config = Column(Text, default="{}")  # JSON
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
