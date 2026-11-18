"""Application configuration loaded from repository YAML files."""

from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
import os

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def cors_origins_from_environment() -> list[str]:
    """Return explicit browser origins; wildcard origins are intentionally rejected."""
    configured = os.getenv("CORS_ALLOWED_ORIGINS")
    if configured is None:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    origins = [value.strip().rstrip("/") for value in configured.split(",") if value.strip()]
    for origin in origins:
        parsed = urlsplit(origin)
        if (origin == "*" or parsed.scheme not in {"http", "https"} or not parsed.netloc
                or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
            raise ValueError("CORS_ALLOWED_ORIGINS must be a comma-separated list of explicit HTTP(S) origins")
    return origins


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = yaml.safe_load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return value


@lru_cache(maxsize=1)
def load_project_config() -> dict[str, Any]:
    """Load and minimally validate the dataset and model configuration."""
    dataset = _read_yaml(PROJECT_ROOT / "configs" / "dataset_config.yaml")
    model = _read_yaml(PROJECT_ROOT / "configs" / "model_config.yaml")
    classes = dataset.get("class_selection", {}).get("classes", [])
    if not classes or len({item.get("id") for item in classes}) != len(classes):
        raise ValueError("Dataset config must define unique selected class IDs")
    if model.get("model", {}).get("image_size", 0) <= 0:
        raise ValueError("Model image_size must be a positive integer")
    return {"dataset": dataset, "model": model}
