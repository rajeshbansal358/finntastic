from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Sentence(Base):
    __tablename__ = "sentences"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(300))
    difficulty: Mapped[str] = mapped_column(String(20))
    target_tokens_json: Mapped[str] = mapped_column(Text, default="[]")
