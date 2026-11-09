from pydantic import BaseModel, ConfigDict


class SentenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    difficulty: str
