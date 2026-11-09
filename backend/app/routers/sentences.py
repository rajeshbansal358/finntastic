from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Sentence
from app.schemas import SentenceOut

router = APIRouter(prefix="/api/sentences", tags=["sentences"])


@router.get("", response_model=list[SentenceOut])
def list_sentences(db: Session = Depends(get_db)) -> list[Sentence]:
    return list(db.scalars(select(Sentence).order_by(Sentence.id)))
