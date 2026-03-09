import os
import uuid
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
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ---------------------------------------------------------------------------
# Database URL handling with automatic scheme fixes
# ---------------------------------------------------------------------------
_raw_url = os.getenv(
    "DATABASE_URL",
    os.getenv("POSTGRES_URL", "sqlite:///./app.db"),
)
if _raw_url.startswith("postgresql+asyncpg://"):
    _raw_url = _raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
elif _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg://", 1)
elif _raw_url.startswith("postgresql://") and "+psycopg" not in _raw_url:
    _raw_url = _raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

# SSL is already handled via ?sslmode=require in the URL — no extra connect_args
engine = create_engine(_raw_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Auto-create tables on import (safe — uses CREATE IF NOT EXISTS)
# ---------------------------------------------------------------------------
def init_db():
    Base.metadata.create_all(engine)


# ---------------------------------------------------------------------------
# Prefix for all tables to avoid collisions in shared DB
# ---------------------------------------------------------------------------
TABLE_PREFIX = "sm_"


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Session(Base):
    __tablename__ = f"{TABLE_PREFIX}sessions"
    session_id = Column(String, primary_key=True, default=_new_uuid)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=30),
    )

    flashcards = relationship(
        "Flashcard", back_populates="session", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "Review", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (Index(f"idx_{TABLE_PREFIX}sessions_expires_at", "expires_at"),)


class Flashcard(Base):
    __tablename__ = f"{TABLE_PREFIX}flashcards"
    flashcard_id = Column(String, primary_key=True, default=_new_uuid)
    session_id = Column(
        String,
        ForeignKey(f"{TABLE_PREFIX}sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    next_review = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=1),
    )
    confidence_score = Column(Float, nullable=False, default=0.0)
    ai_model_version = Column(String, nullable=False, default="openai-gpt-oss-120b")
    generated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session = relationship("Session", back_populates="flashcards")
    reviews = relationship(
        "Review", back_populates="flashcard", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(f"idx_{TABLE_PREFIX}flashcards_session", "session_id"),
        Index(f"idx_{TABLE_PREFIX}flashcards_next_review", "next_review"),
    )


class Review(Base):
    __tablename__ = f"{TABLE_PREFIX}reviews"
    review_id = Column(String, primary_key=True, default=_new_uuid)
    flashcard_id = Column(
        String,
        ForeignKey(f"{TABLE_PREFIX}flashcards.flashcard_id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id = Column(
        String,
        ForeignKey(f"{TABLE_PREFIX}sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    is_correct = Column(Boolean, nullable=False)
    reviewed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    flashcard = relationship("Flashcard", back_populates="reviews")
    session = relationship("Session", back_populates="reviews")

    __table_args__ = (
        Index(f"idx_{TABLE_PREFIX}reviews_flashcard", "flashcard_id"),
        Index(f"idx_{TABLE_PREFIX}reviews_session", "session_id"),
    )
