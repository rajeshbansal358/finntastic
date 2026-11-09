from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine
from app.routers import sentences
from app.seed import seed_sentences


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)
    seed_sentences()
    yield


app = FastAPI(title="finntastic", lifespan=lifespan)
app.include_router(sentences.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
