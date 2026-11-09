from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Sentence

SEED_SENTENCES = [
    ("I drink coffee every morning.", "easy"),
    ("The dog is sleeping under the table.", "easy"),
    ("We are going to the lake tomorrow.", "medium"),
    ("She has never visited the northern part of the country.", "hard"),
]


def seed_sentences() -> None:
    with SessionLocal() as db:
        if db.scalar(select(func.count(Sentence.id))) == 0:
            db.add_all(Sentence(text=t, difficulty=d) for t, d in SEED_SENTENCES)
            db.commit()
