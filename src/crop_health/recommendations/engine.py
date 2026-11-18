"""Deterministic, traceable recommendations based on curated KB records."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml

from crop_health.knowledge_base.service import KnowledgeBase
from crop_health.weather.service import WeatherService

_DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "configs/recommendation_config.yaml"


class RecommendationEngine:
    def __init__(self, knowledge_base: KnowledgeBase | None = None,
                 weather_service: Any | None = None,
                 config_path: str | Path = _DEFAULT_CONFIG) -> None:
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.weather_service = weather_service or WeatherService()
        config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        if not isinstance(config, dict) or config.get("version") != 1:
            raise ValueError("recommendation config must have version 1")
        self.config = config
        self.minimum_confidence = self._number(config.get("minimum_prediction_confidence"))
        if self.minimum_confidence is None or not 0 <= self.minimum_confidence <= 1:
            raise ValueError("minimum_prediction_confidence must be between 0 and 1")
        if not isinstance(config.get("weather_rules"), list):
            raise ValueError("weather_rules must be a list")
        self.severity_categories = set(config.get("severity", {}).get("supported_categories", []))

    def recommend(self, prediction: Any, severity: Any = None,
                  location: str | None = None) -> dict[str, Any]:
        class_id, confidence, reason = self._prediction(prediction)
        entry = self.knowledge_base.get(class_id) if class_id else None
        if reason is None and entry is None:
            reason = "unsupported_disease"
        if reason is None and confidence is not None and confidence < self.minimum_confidence:
            reason = "low_confidence"
        severity_data = self._severity(severity)
        if reason:
            return {
                "status": "safe_fallback", "prediction_status": reason,
                "prediction": {"class_id": class_id, "confidence": confidence},
                "severity": severity_data, "disease_information": None,
                "general_guidance": [], "weather_context": self._weather_unavailable("not_requested"),
                "weather_guidance": [],
                "message": "No disease-specific recommendation is available; seek an agricultural professional if concerned.",
            }

        assert entry is not None and class_id is not None
        context: Any = self.weather_service.current(location) if isinstance(location, str) and location.strip() else None
        sources = entry.get("sources", [])
        general = []
        for field in ("prevention", "general_management"):
            for i, text in enumerate(entry.get(field, [])):
                general.append({"id": f"{class_id}:{field}:{i}", "category": field, "text": text,
                                "trace": {"knowledge_base_entry_id": class_id, "field": field, "sources": sources}})
        if severity_data and severity_data["category"] == self.config.get("severity", {}).get("high_severity_category"):
            general.insert(0, {"id": f"{class_id}:severity:high", "category": "severity_context",
                               "text": self.config["severity"]["high_severity_notice"],
                               "trace": {"knowledge_base_entry_id": class_id, "field": "general_management",
                                         "rule_id": "high_severity_notice", "sources": sources}})
        weather_summary = self._weather_summary(context)
        weather_guidance = self._weather_guidance(class_id, entry, context) if weather_summary["status"] == "available" else []
        return {
            "status": "available", "prediction_status": "accepted",
            "prediction": {"class_id": class_id, "confidence": confidence}, "severity": severity_data,
            "disease_information": {
                "id": class_id, "crop": entry["crop"], "name": entry["disease_name"],
                "condition_type": entry["condition_type"], "description": entry["description"],
                "symptoms": entry.get("symptoms", []),
                "trace": {"knowledge_base_entry_id": class_id, "field": "disease_information", "sources": sources},
            },
            "general_guidance": general, "weather_context": weather_summary,
            "weather_guidance": weather_guidance,
            "message": None if weather_summary["status"] == "available" else
                "Weather-specific guidance could not be generated; disease-based guidance is still available.",
        }

    def _weather_guidance(self, class_id: str, entry: dict[str, Any], context: Any) -> list[dict[str, Any]]:
        if not isinstance(context, dict) or context.get("status") != "available" or not isinstance(context.get("weather"), dict):
            return []
        favorable = entry.get("favorable_weather_conditions") or []
        if not favorable:
            return []
        result = []
        for rule in self.config["weather_rules"]:
            if class_id not in rule.get("disease_ids", []) or not self._matches(context["weather"], rule):
                continue
            result.append({
                "id": rule["id"],
                "text": "Current observations match a configured weather context associated with this condition. "
                        "This context does not show that weather caused the symptoms. The knowledge base describes "
                        "favorable conditions as: " + "; ".join(favorable),
                "observed_at": context.get("observed_at"),
                "trace": {"knowledge_base_entry_id": class_id, "knowledge_base_field": "favorable_weather_conditions",
                          "rule_id": rule["id"], "rule_note": rule.get("note"), "sources": entry.get("sources", [])},
            })
        return result

    @classmethod
    def _matches(cls, weather: dict[str, Any], rule: dict[str, Any]) -> bool:
        def test(cond: dict[str, Any]) -> bool:
            value, threshold = cls._number(weather.get(cond.get("field"))), cls._number(cond.get("value"))
            if value is None or threshold is None:
                return False
            return {"gte": value >= threshold, "lte": value <= threshold,
                    "gt": value > threshold, "lt": value < threshold}.get(cond.get("operator"), False)
        all_of, any_of = rule.get("all_of", []), rule.get("any_of", [])
        return all(test(c) for c in all_of) and (not any_of or any(test(c) for c in any_of))

    @classmethod
    def _prediction(cls, value: Any) -> tuple[str | None, float | None, str | None]:
        if not isinstance(value, dict):
            return None, None, "invalid_prediction"
        class_id, confidence = value.get("class_id"), cls._number(value.get("confidence"))
        if not isinstance(class_id, str) or not class_id.strip() or confidence is None or not 0 <= confidence <= 1:
            return None, confidence, "invalid_prediction"
        return class_id.strip(), confidence, None

    def _severity(self, value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if isinstance(value, str):
            category, percentage = value, None
        elif isinstance(value, dict):
            category = value.get("category")
            percentage = self._number(value.get("severity_percentage"))
            if "severity_percentage" in value and (percentage is None or not 0 <= percentage <= 100):
                return None
        else:
            return None
        if not isinstance(category, str) or category not in self.severity_categories:
            return None
        result = {"category": category}
        if percentage is not None:
            result["severity_percentage"] = percentage
        return result

    @staticmethod
    def _number(value: Any) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return None
        return float(value)

    @classmethod
    def _weather_summary(cls, context: Any) -> dict[str, Any]:
        if not isinstance(context, dict) or context.get("status") != "available" or not isinstance(context.get("weather"), dict):
            status = "unavailable" if isinstance(context, dict) and context.get("status") == "unavailable" else "not_requested"
            return cls._weather_unavailable(status)
        weather = context["weather"]
        fields = ("temperature_c", "relative_humidity_percent", "precipitation_mm", "wind_speed_kmh")
        if any(cls._number(weather.get(field)) is None for field in fields):
            return cls._weather_unavailable("unavailable")
        return {"status": "available", "location": context.get("location"),
                "observed_at": context.get("observed_at"), "weather": weather, "provider": context.get("provider")}

    @staticmethod
    def _weather_unavailable(status: str) -> dict[str, Any]:
        return {"status": status, "location": None, "observed_at": None, "weather": None, "provider": None}
