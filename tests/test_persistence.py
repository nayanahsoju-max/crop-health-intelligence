from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from backend.app.database import create_database_engine, create_session_factory
from backend.app.main import app
from backend.app.models import PredictionRecord
from backend.app.prediction_repository import PredictionRepository


@pytest.fixture
def migrated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_file = tmp_path / "isolated_history.sqlite3"
    url = f"sqlite:///{database_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    engine = create_database_engine(url)
    factory = create_session_factory(engine)
    try:
        yield url, factory
    finally:
        engine.dispose()


def sample_record(repository: PredictionRepository, **overrides):
    data = {
        "predicted_class_id": "tomato_early_blight",
        "confidence": 0.875,
        "severity": {"category": "Moderate", "severity_percentage": 22.4, "method": "baseline"},
        "weather_context": {"status": "available", "provider": "Open-Meteo", "weather": {"temperature_c": 24}},
        "recommendation_result": {
            "prediction_status": "accepted",
            "recommendations": [{"text": "Inspect affected leaves", "trace": {"knowledge_base_entry_id": "tomato_early_blight", "sources": [{"url": "https://example.test/source"}]}}],
        },
        "model_version": "efficientnet-b0-smoke",
        "image_reference": {"filename": "leaf.jpg", "media_type": "image/jpeg", "sha256": "a" * 64, "storage_uri": "file://images/leaf.jpg"},
    }
    data.update(overrides)
    return repository.create(**data)


def test_migration_and_successful_create_retrieval_preserve_provenance(migrated_database):
    _, factory = migrated_database
    with factory() as session:
        record = sample_record(PredictionRepository(session))
        record_id = record.id
    with factory() as session:
        fetched = PredictionRepository(session).get(record_id)
        assert fetched is not None
        assert fetched.predicted_class_id == "tomato_early_blight"
        assert float(fetched.confidence) == pytest.approx(0.875)
        assert fetched.severity_details["category"] == "Moderate"
        assert fetched.weather_context["provider"] == "Open-Meteo"
        assert fetched.recommendation_result["recommendations"][0]["trace"]["sources"][0]["url"].startswith("https://")
        assert fetched.image_sha256 == "a" * 64
        assert fetched.created_at is not None


def test_history_filter_order_and_pagination(migrated_database):
    _, factory = migrated_database
    with factory() as session:
        repo = PredictionRepository(session)
        sample_record(repo)
        sample_record(repo, predicted_class_id="potato_late_blight", confidence=0.73)
        sample_record(repo)
        ordered = repo.history(limit=10)
        ids = [item.id for item in ordered]
        assert len(ids) == len(set(ids)) == 3
        assert [item.id for item in repo.history(limit=2)] == ids[:2]
        assert [item.predicted_class_id for item in repo.history(limit=10, class_id="tomato_early_blight")] == [
            "tomato_early_blight", "tomato_early_blight"
        ]
        assert repo.get("missing-id") is None
        assert repo.history(limit=1, offset=1)[0].id == ids[1]


@pytest.mark.parametrize("overrides", [
    {"confidence": -0.01}, {"confidence": 1.01},
    {"predicted_class_id": "   "},
    {"severity": {"category": "Extreme"}},
    {"severity": {"severity_percentage": 101}},
    {"image_reference": {"sha256": "bad"}},
])
def test_database_constraints_reject_invalid_values(migrated_database, overrides):
    _, factory = migrated_database
    with factory() as session:
        with pytest.raises(IntegrityError):
            sample_record(PredictionRepository(session), **overrides)
        session.rollback()


def test_database_requires_class_and_confidence(migrated_database):
    _, factory = migrated_database
    with factory() as session:
        with pytest.raises(IntegrityError):
            session.add(PredictionRecord())
            session.commit()
        session.rollback()


def test_history_pagination_bounds_are_validated(migrated_database):
    _, factory = migrated_database
    with factory() as session:
        repository = PredictionRepository(session)
        with pytest.raises(ValueError):
            repository.history(limit=201)
        with pytest.raises(ValueError):
            repository.history(offset=-1)


def test_api_persists_and_retrieves_prediction_history(migrated_database):
    with TestClient(app) as client:
        created = client.post("/predictions", json={
            "class_id": "tomato_late_blight",
            "confidence": 0.82,
            "severity": {"category": "Severe", "severity_percentage": 44.25},
            "weather_context": {"status": "unavailable", "weather": None},
            "recommendation_result": {"prediction_status": "accepted", "trace": {"sources": ["kb"]}},
            "model_version": "smoke-1",
            "image_reference": {"filename": "sample.png", "media_type": "image/png", "sha256": "b" * 64},
        })
        assert created.status_code == 201
        record_id = created.json()["id"]
        assert created.json()["recommendation_result"]["trace"]["sources"] == ["kb"]
        assert created.json()["image_reference"]["filename"] == "sample.png"
        detail = client.get(f"/predictions/{record_id}")
        assert detail.status_code == 200
        assert detail.json()["predicted_class_id"] == "tomato_late_blight"
        listing = client.get("/predictions", params={"class_id": "tomato_late_blight"})
        assert listing.status_code == 200
        assert len(listing.json()) == 1


def test_api_rejects_invalid_confidence_severity_and_image_reference(migrated_database):
    with TestClient(app) as client:
        for data in (
            {"class_id": "tomato_early_blight", "confidence": 1.5},
            {"class_id": "tomato_early_blight", "confidence": 0.7, "severity": {"category": "Critical"}},
            {"class_id": "tomato_early_blight", "confidence": 0.7, "image_reference": {"sha256": "not-a-hash"}},
        ):
            response = client.post("/predictions", json=data)
            assert response.status_code == 422


def test_json_prediction_payload_has_a_bounded_request_size(migrated_database):
    with TestClient(app) as client:
        response = client.post(
            "/predictions",
            json={"class_id": "tomato_early_blight", "confidence": 0.8, "result_metadata": {"payload": "x" * (1024 * 1024)}},
        )
        recommendation_response = client.post(
            "/recommendations/current",
            content=b" " * (1024 * 1024 + 1),
            headers={"content-type": "application/json"},
        )
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "request_too_large"
    assert recommendation_response.status_code == 413
    assert recommendation_response.json()["detail"]["code"] == "request_too_large"


def test_api_does_not_expose_database_integrity_exception(migrated_database, monkeypatch):
    def fail_create(*_args, **_kwargs):
        raise IntegrityError("INSERT INTO sensitive_table", {}, Exception("private constraint detail"))

    monkeypatch.setattr(PredictionRepository, "create", fail_create)
    with TestClient(app) as client:
        response = client.post("/predictions", json={
            "class_id": "tomato_early_blight",
            "confidence": 0.8,
        })
    assert response.status_code == 422
    assert response.json()["detail"] == "Prediction record contains invalid data or violates a constraint."
    assert "sensitive_table" not in response.text
    assert "private constraint detail" not in response.text


def test_api_returns_clear_status_when_database_is_not_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with TestClient(app) as client:
        response = client.get("/predictions")
    assert response.status_code == 503
