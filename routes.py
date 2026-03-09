from fastapi import APIRouter, HTTPException, Depends
from fastapi import Body, Path
from sqlalchemy.orm import Session as OrmSession
from datetime import datetime, timedelta
from typing import List, Dict

from models import Session as DBSession, Flashcard, Review, SessionLocal
from ai_service import generate_flashcards

router = APIRouter(prefix="/api/v1")

def get_db() -> OrmSession:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Helper: create an anonymous session (no auth required for MVP)
# ---------------------------------------------------------------------------
def _ensure_session(db: OrmSession, session_id: str | None = None) -> DBSession:
    if session_id:
        sess = db.get(DBSession, session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        return sess
    # Create new session
    new_sess = DBSession()
    db.add(new_sess)
    db.commit()
    db.refresh(new_sess)
    return new_sess

# ---------------------------------------------------------------------------
# POST /generate – AI flashcard generation
# ---------------------------------------------------------------------------
@router.post("/generate")
async def generate(
    payload: Dict = Body(...),
    db: OrmSession = Depends(get_db),
):
    text = payload.get("text")
    max_cards = payload.get("max_cards", 5)
    if not text:
        raise HTTPException(status_code=400, detail="'text' field is required")
    if not isinstance(max_cards, int) or not (1 <= max_cards <= 50):
        raise HTTPException(status_code=400, detail="'max_cards' must be an integer between 1 and 50")

    # Generate flashcards via AI service
    cards = await generate_flashcards(text, max_cards)
    if not cards:
        # AI fallback – return empty list with note
        return {"session_id": None, "cards": [], "note": "AI service unavailable; no cards generated"}

    # Persist session + cards
    session_obj = _ensure_session(db)
    persisted = []
    for card in cards:
        question = card.get("question")
        answer = card.get("answer")
        if not question or not answer:
            continue
        fc = Flashcard(
            session_id=session_obj.session_id,
            question=question,
            answer=answer,
            confidence_score=0.0,
            ai_model_version="openai-gpt-oss-120b",
            next_review=datetime.utcnow() + timedelta(days=1),
        )
        db.add(fc)
        persisted.append({"question": question, "answer": answer})
    db.commit()
    return {"session_id": session_obj.session_id, "cards": persisted}

# ---------------------------------------------------------------------------
# POST /study – start a study session, fetch due cards
# ---------------------------------------------------------------------------
@router.post("/study")
def start_study(
    payload: Dict = Body(...),
    db: OrmSession = Depends(get_db),
):
    session_id = payload.get("session_id")
    num_cards = payload.get("num_cards", 5)
    if not session_id:
        raise HTTPException(status_code=400, detail="'session_id' is required")
    if not isinstance(num_cards, int) or not (1 <= num_cards <= 10):
        raise HTTPException(status_code=400, detail="'num_cards' must be 1‑10")

    sess = db.get(DBSession, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.utcnow()
    due_cards = (
        db.query(Flashcard)
        .filter(Flashcard.session_id == session_id, Flashcard.next_review <= now)
        .order_by(Flashcard.next_review)
        .limit(num_cards)
        .all()
    )

    result_cards = []
    for fc in due_cards:
        result_cards.append({
            "id": fc.flashcard_id,
            "question": fc.question,
            "answer": fc.answer,
            "next_review": fc.next_review.isoformat(),
            "interval": 1,  # placeholder – real SM‑2 values are stored in DB after reviews
            "ease_factor": 2.5,
        })
    return {"session_id": session_id, "cards": result_cards}

# ---------------------------------------------------------------------------
# POST /study/{card_id}/review – record a review and adjust SM‑2 schedule
# ---------------------------------------------------------------------------
@router.post("/study/{card_id}/review")
def review_card(
    card_id: str = Path(..., description="Flashcard UUID"),
    payload: Dict = Body(...),
    db: OrmSession = Depends(get_db),
):
    session_id = payload.get("session_id")
    response = payload.get("response")  # Expected "Correct" or "Incorrect"
    if not session_id or response not in {"Correct", "Incorrect"}:
        raise HTTPException(status_code=400, detail="'session_id' and valid 'response' are required")

    fc = db.get(Flashcard, card_id)
    if not fc or fc.session_id != session_id:
        raise HTTPException(status_code=404, detail="Flashcard not found for given session")

    # Simple SM‑2 implementation (very lightweight)
    is_correct = response == "Correct"
    review = Review(
        flashcard_id=card_id,
        session_id=session_id,
        is_correct=is_correct,
    )
    db.add(review)

    # Retrieve last interval & EF – stored in review history would be ideal, but for brevity we use defaults
    interval = 1
    ease_factor = 2.5
    # Adjust based on correctness
    if is_correct:
        interval = int(interval * ease_factor)
        ease_factor = min(2.5, ease_factor + 0.1)  # cap at 2.5 for simplicity
    else:
        interval = 1
        ease_factor = max(1.3, ease_factor - 0.2)
    # Update next_review
    fc.next_review = datetime.utcnow() + timedelta(days=interval)
    db.commit()
    db.refresh(fc)
    return {
        "updated": {
            "id": fc.flashcard_id,
            "next_review": fc.next_review.isoformat(),
            "interval": interval,
            "ease_factor": round(ease_factor, 2),
        }
    }
