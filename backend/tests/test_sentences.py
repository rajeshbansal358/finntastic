import os
from pathlib import Path

from fastapi.testclient import TestClient

_TMP_DB = Path(os.environ.get("TMPDIR", ".")) / "finntastic_test.db"
if _TMP_DB.exists():
    _TMP_DB.unlink()
os.environ["FINN_DB_PATH"] = str(_TMP_DB)

from app.main import app  # noqa: E402


def test_health_and_random_sentence() -> None:
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

        res = client.get("/api/sentences/random", params={"difficulty": "easy"})
        assert res.status_code == 200
        data = res.json()
        assert data["difficulty"] == "easy"
        assert len(data["initial_words"]) >= 5
        assert data["target_count"] >= 4


def test_two_stage_hints_and_difficulty_scaling() -> None:
    with TestClient(app) as client:
        sentences = client.get("/api/sentences").json()
        easy = next(s for s in sentences if s["difficulty"] == "easy" and "table" in s["text"])
        hard = next(s for s in sentences if s["difficulty"] == "hard")

        stem_hint = client.get(
            f"/api/sentences/{easy['id']}/hint",
            params={"word_index": 2, "stage": "stem"},
        ).json()
        assert len(stem_hint["options"]) == 2
        assert "pöytä" in stem_hint["options"]
        assert stem_hint["gradation_note"] == "t -> d"

        infl_hint = client.get(
            f"/api/sentences/{easy['id']}/hint",
            params={"word_index": 2, "stage": "inflection"},
        ).json()
        assert "pöydän" in infl_hint["options"]
        assert infl_hint["grammar_note"] is not None

        hard_hint = client.get(
            f"/api/sentences/{hard['id']}/hint",
            params={"word_index": 0, "stage": "stem"},
        ).json()
        assert len(hard_hint["options"]) == 4
        assert hard_hint["gradation_note"] is None


def test_check_sentence_statuses_and_solved() -> None:
    with TestClient(app) as client:
        sentences = client.get("/api/sentences").json()
        coffee = next(s for s in sentences if "coffee" in s["text"])

        res = client.post(
            f"/api/sentences/{coffee['id']}/check",
            json={"words": ["Minä", "kahvia", "drink", "joka", "väärä", "extra"]},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["solved"] is False
        statuses = [s["status"] for s in body["statuses"]]
        assert statuses == ["correct", "mispositioned", "untranslated", "correct", "wrong", "unnecessary"]

        res = client.post(
            f"/api/sentences/{coffee['id']}/check",
            json={"words": ["Minä", "juon", "kahvia", "joka", "aamu"]},
        )
        assert res.status_code == 200
        assert res.json()["solved"] is True
        assert res.json()["missing_count"] == 0
