"""Load and query the curated, source-linked disease knowledge base."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).with_name("diseases.json")


class KnowledgeBase:
    def __init__(self, path: str | Path = _DATA_PATH) -> None:
        self.path = Path(path)
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1 or not isinstance(payload.get("entries"), list):
            raise ValueError("Unsupported disease knowledge-base schema")
        self._entries: dict[str, dict[str, Any]] = {}
        for entry in payload["entries"]:
            if not isinstance(entry, dict) or not entry.get("id") or entry["id"] in self._entries:
                raise ValueError("Knowledge-base entries need unique, non-empty ids")
            self._entries[entry["id"]] = entry

    def get(self, disease_id: str) -> dict[str, Any] | None:
        """Return a disease/status record, or None for an unsupported class."""
        item = self._entries.get(disease_id)
        return dict(item) if item is not None else None

    def require(self, disease_id: str) -> dict[str, Any]:
        item = self.get(disease_id)
        if item is None:
            raise KeyError(f"No knowledge-base entry for {disease_id!r}")
        return item

    def all(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._entries.values()]
