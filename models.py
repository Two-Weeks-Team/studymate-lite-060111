import os
from datetime import datetime, timedelta
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    func,
    Index,
    create_engine,
    text as sql_text,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ---------------------------------------------------------------------------
# Database URL handling with automatic scheme fixes and SSL args
# ---------------------------------------------------------------------------
_raw_url = os.getenv(
    "DATABASE_URL",
    os.getenv("POSTGRES_URL", "sqlite:///./app.db")
)
if _raw_url.startswith("postgresql+asyncpg://"):
    _raw_url = _raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
elif _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg://")

# Determine if we need SSL (non‑localhost & not sqlite)
_use_ssl = not (
    _raw_url.startswith("sqlite") or "localhost" in _raw_url or "127.0.0.1" in _raw_url
)
_connect_args = {"sslmode": "require"} if _use_ssl else {}

engine = create_engine(_raw_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# ---------------------------------------------------------------------------
# Prefix for all tables to avoid collisions in shared DB
# ---------------------------------------------------------------------------
TABLE_PREFIX = "sm_"

class Session(Base):
    __tablename__ = f"{TABLE_PREFIX}sessions"
    session_id = Column(String, primary_key=True, default=lambda: func.gen_random_uuid())
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow() + timedelta(days=30))

    # Relationships – no type annotations per requirement
    flashcards = relationship("Flashcard", back_populates="session", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index(f"idx_{TABLE_PREFIX}sessions_expires_at", "expires_at"),
    )

class Flashcard(Base):
    __tablename__ = f"{TABLE_PREFIX}flashcards"
    flashcard_id = Column(String, primary_key=True, default=lambda: func.gen_random_uuid())
    session_id = Column(String, ForeignKey(f"{TABLE_PREFIX}sessions.session_id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    next_review = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow() + timedelta(days=1))
    confidence_score = Column(Float, nullable=False, default=0.0)
    ai_model_version = Column(String, nullable=False, default="rake-v1.2")
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("Session", back_populates="flashcards")
    reviews = relationship("Review", back_populates="flashcard", cascade="all, delete-orphan")

    __table_args__ = (
        Index(f"idx_{TABLE_PREFIX}flashcards_session", "session_id"),
        Index(f"idx_{TABLE_PREFIX}flashcards_next_review", "next_review"),
    )

class Review(Base):
    __tablename__ = f"{TABLE_PREFIX}reviews"
    review_id = Column(String, primary_key=True, default=lambda: func.gen_random_uuid())
    flashcard_id = Column(String, ForeignKey(f"{TABLE_PREFIX}flashcards.flashcard_id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String, ForeignKey(f"{TABLE_PREFIX}sessions.session_id", ondelete="CASCADE"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    flashcard = relationship("Flashcard", back_populates="reviews")
    session = relationship("Session", back_populates="reviews")

    __table_args__ = (
        Index(f"idx_{TABLE_PREFIX}reviews_flashcard", "flashcard_id"),
        Index(f"idx_{TABLE_PREFIX}reviews_session", "session_id"),
    )

# Create tables if they do not exist (useful for SQLite local dev)
if __name__ == "__main__":
    Base.metadata.create_all(engine) 