import pytest

from backend.app.config import cors_origins_from_environment


def test_cors_origins_default_to_local_development(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    assert cors_origins_from_environment() == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_cors_origins_accept_explicit_comma_separated_origins(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", " https://ui.example.test/ ,http://localhost:4173 ")
    assert cors_origins_from_environment() == [
        "https://ui.example.test",
        "http://localhost:4173",
    ]


@pytest.mark.parametrize("value", ["*", "https://example.test/path", "javascript://example.test", "https://user:pw@example.test"])
def test_cors_rejects_wildcards_and_non_origins(monkeypatch, value):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", value)
    with pytest.raises(ValueError, match="explicit HTTP"):
        cors_origins_from_environment()
