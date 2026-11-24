import json
import logging
import random
import re
from collections import Counter
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Sentence
from app.schemas import (
    CheckRequest,
    CheckResponse,
    Difficulty,
    HintOut,
    RandomSentenceOut,
    SentenceOut,
    WordFeedback,
)

router = APIRouter(prefix="/api/sentences", tags=["sentences"])
logger = logging.getLogger("finntastic.sentences")

_PUNCT_RE = re.compile(r"^[\s.,!?;:\"'()]+|[\s.,!?;:\"'()]+$")


def _normalize(word: str) -> str:
    return _PUNCT_RE.sub("", word).lower()


def _tokenize_english(text: str) -> list[str]:
    return [w for w in (_PUNCT_RE.sub("", part) for part in text.split()) if w]


def _load_tokens(sentence: Sentence) -> list[dict]:
    return json.loads(sentence.target_tokens_json or "[]")


@router.get("", response_model=list[SentenceOut])
def list_sentences(db: Session = Depends(get_db)) -> list[Sentence]:
    return list(db.scalars(select(Sentence).order_by(Sentence.id)))


@router.get("/random", response_model=RandomSentenceOut)
def get_random_sentence(
    difficulty: Difficulty | None = Query(default=None),
    exclude_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RandomSentenceOut:
    stmt = select(Sentence)
    if difficulty is not None:
        stmt = stmt.where(Sentence.difficulty == difficulty)
    candidates = list(db.scalars(stmt))
    if not candidates:
        logger.warning("No sentences found for difficulty=%s", difficulty)
        raise HTTPException(status_code=404, detail="No sentences found")
    if exclude_id is not None and len(candidates) > 1:
        candidates = [s for s in candidates if s.id != exclude_id]
    chosen = random.choice(candidates)
    logger.info("Serving random sentence id=%s difficulty=%s", chosen.id, chosen.difficulty)
    tokens = _load_tokens(chosen)
    return RandomSentenceOut(
        id=chosen.id,
        text=chosen.text,
        difficulty=chosen.difficulty,
        initial_words=_tokenize_english(chosen.text),
        target_count=len(tokens),
    )


@router.get("/{sentence_id}/hint", response_model=HintOut)
def get_hint(
    sentence_id: int,
    word_index: int = Query(ge=0),
    stage: Literal["stem", "inflection"] = Query(default="stem"),
    db: Session = Depends(get_db),
) -> HintOut:
    sentence = db.get(Sentence, sentence_id)
    if sentence is None:
        raise HTTPException(status_code=404, detail="Sentence not found")
    tokens = _load_tokens(sentence)
    if not tokens:
        raise HTTPException(status_code=400, detail="Sentence has no target tokens")
    idx = min(word_index, len(tokens) - 1)
    tok = tokens[idx]

    option_count = {"easy": 2, "medium": 3, "hard": 4}.get(sentence.difficulty, 3)
    if stage == "stem":
        correct = tok["stem"]
        distractors = tok.get("stem_distractors", [])
    else:
        correct = tok["target"]
        distractors = tok.get("inflection_distractors", [])

    pool = [correct] + [d for d in distractors if _normalize(d) != _normalize(correct)][: option_count - 1]
    random.shuffle(pool)

    gradation_note = tok.get("gradation") if sentence.difficulty in ("easy", "medium") else None
    grammar_note = tok.get("inflection") if (stage == "inflection" and sentence.difficulty == "easy") else None
    return HintOut(
        word_index=idx,
        stage=stage,
        options=pool,
        gradation_note=gradation_note,
        grammar_note=grammar_note,
    )


@router.post("/{sentence_id}/check", response_model=CheckResponse)
def check_sentence(
    sentence_id: int,
    payload: CheckRequest,
    db: Session = Depends(get_db),
) -> CheckResponse:
    sentence = db.get(Sentence, sentence_id)
    if sentence is None:
        raise HTTPException(status_code=404, detail="Sentence not found")
    tokens = _load_tokens(sentence)
    targets = [_normalize(t["target"]) for t in tokens]
    english_words = {_normalize(w) for w in _tokenize_english(sentence.text)}

    user_norm = [_normalize(w) for w in payload.words]
    remaining = Counter(targets)
    statuses: list[WordFeedback | None] = [None] * len(user_norm)

    for i, w in enumerate(user_norm):
        if i < len(targets) and w == targets[i]:
            statuses[i] = WordFeedback(index=i, word=payload.words[i], status="correct", message="Correct!")
            remaining[w] -= 1

    extra_budget = max(0, len(user_norm) - len(targets))
    for i, w in enumerate(user_norm):
        if statuses[i] is not None:
            continue
        if w and remaining[w] > 0:
            statuses[i] = WordFeedback(
                index=i,
                word=payload.words[i],
                status="mispositioned",
                message="Right Finnish word, wrong position",
            )
            remaining[w] -= 1
        elif w in english_words and w not in targets:
            statuses[i] = WordFeedback(
                index=i,
                word=payload.words[i],
                status="untranslated",
                message="Still in English — translate or remove if unnecessary",
            )
        elif i >= len(targets) and extra_budget > 0:
            statuses[i] = WordFeedback(
                index=i,
                word=payload.words[i],
                status="unnecessary",
                message="Extra word — try merging or removing",
            )
            extra_budget -= 1
        else:
            statuses[i] = WordFeedback(
                index=i,
                word=payload.words[i],
                status="wrong",
                message="Incorrect translation or inflection",
            )

    final_statuses = [s for s in statuses if s is not None]
    solved = len(user_norm) == len(targets) and all(s.status == "correct" for s in final_statuses)
    missing_count = max(0, len(targets) - len(user_norm))
    logger.info("Checked sentence id=%s solved=%s words=%d", sentence_id, solved, len(user_norm))
    return CheckResponse(solved=solved, missing_count=missing_count, statuses=final_statuses)
