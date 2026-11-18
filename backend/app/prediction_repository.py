"""Create and retrieve prediction history records."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import PredictionRecord


class PredictionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, predicted_class_id: str, confidence: float,
               severity: dict[str, Any] | None = None,
               weather_context: dict[str, Any] | None = None,
               recommendation_result: dict[str, Any] | None = None,
               result_metadata: dict[str, Any] | None = None,
               model_version: str | None = None,
               image_reference: dict[str, Any] | None = None) -> PredictionRecord:
        severity = severity or {}
        image_reference = image_reference or {}
        record = PredictionRecord(
            predicted_class_id=predicted_class_id,
            confidence=confidence,
            severity_category=severity.get("category"),
            severity_percentage=severity.get("severity_percentage"),
            severity_details=severity or None,
            weather_context=weather_context,
            recommendation_result=recommendation_result,
            result_metadata=result_metadata,
            model_version=model_version,
            image_filename=image_reference.get("filename"),
            image_media_type=image_reference.get("media_type"),
            image_sha256=image_reference.get("sha256"),
            image_storage_uri=image_reference.get("storage_uri"),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, record_id: str) -> PredictionRecord | None:
        return self.session.get(PredictionRecord, record_id)

    def history(self, *, limit: int = 50, offset: int = 0,
                class_id: str | None = None) -> list[PredictionRecord]:
        if not 1 <= limit <= 200 or offset < 0:
            raise ValueError("limit must be 1-200 and offset must be non-negative")
        statement = select(PredictionRecord)
        if class_id:
            statement = statement.where(PredictionRecord.predicted_class_id == class_id)
        statement = statement.order_by(PredictionRecord.created_at.desc(), PredictionRecord.id.desc())
        return list(self.session.scalars(statement.limit(limit).offset(offset)))


def prediction_to_dict(record: PredictionRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "predicted_class_id": record.predicted_class_id,
        "confidence": float(record.confidence),
        "severity": record.severity_details,
        "weather_context": record.weather_context,
        "recommendation_result": record.recommendation_result,
        "result_metadata": record.result_metadata,
        "model_version": record.model_version,
        "image_reference": {
            "filename": record.image_filename,
            "media_type": record.image_media_type,
            "sha256": record.image_sha256,
            "storage_uri": record.image_storage_uri,
        } if any((record.image_filename, record.image_media_type, record.image_sha256, record.image_storage_uri)) else None,
        "created_at": record.created_at,
    }
