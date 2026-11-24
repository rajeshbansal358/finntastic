from typing import Literal

from pydantic import BaseModel, ConfigDict

Difficulty = Literal["easy", "medium", "hard"]
WordStatus = Literal["correct", "mispositioned", "untranslated", "unnecessary", "wrong"]


class SentenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    difficulty: str


class RandomSentenceOut(BaseModel):
    id: int
    text: str
    difficulty: str
    initial_words: list[str]
    target_count: int


class HintOut(BaseModel):
    word_index: int
    stage: Literal["stem", "inflection"]
    options: list[str]
    gradation_note: str | None = None
    grammar_note: str | None = None


class CheckRequest(BaseModel):
    words: list[str]


class WordFeedback(BaseModel):
    index: int
    word: str
    status: WordStatus
    message: str


class CheckResponse(BaseModel):
    solved: bool
    missing_count: int
    statuses: list[WordFeedback]
