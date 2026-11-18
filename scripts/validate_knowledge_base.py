"""Validate knowledge-base records against configured classifier classes."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from crop_health.knowledge_base.service import KnowledgeBase  # noqa: E402


def validate() -> list[str]:
    kb = KnowledgeBase(ROOT / "src/crop_health/knowledge_base/diseases.json")
    config = yaml.safe_load((ROOT / "configs/dataset_config.yaml").read_text(encoding="utf-8"))
    classes = config["class_selection"]["classes"]
    errors: list[str] = []
    ids = {e["id"] for e in kb.all()}
    for cls in classes:
        item = kb.get(cls["id"])
        if item is None:
            errors.append(f"Missing configured class: {cls['id']}")
            continue
        if item["crop"].casefold() != cls["crop"].casefold():
            errors.append(f"Crop mismatch: {cls['id']}")
        for field in ("disease_name", "description", "symptoms", "favorable_weather_conditions", "prevention", "general_management", "sources"):
            if field not in item:
                errors.append(f"{cls['id']} missing field {field}")
        if not item.get("sources"):
            errors.append(f"{cls['id']} has no source")
        for source in item.get("sources", []):
            if not source.get("url", "").startswith("https://") or not source.get("organization") or not source.get("title"):
                errors.append(f"{cls['id']} has incomplete source metadata")
    extra = ids - {c["id"] for c in classes}
    if extra:
        errors.append(f"Unconfigured knowledge-base entries: {sorted(extra)}")
    return errors


if __name__ == "__main__":
    errors = validate()
    if errors:
        print("Knowledge base validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        raise SystemExit(1)
    kb = KnowledgeBase(ROOT / "src/crop_health/knowledge_base/diseases.json")
    print(f"Valid: {len(kb.all())} entries cover all configured classes")
