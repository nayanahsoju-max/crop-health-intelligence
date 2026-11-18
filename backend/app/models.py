"""Relational models for prediction history."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, JSON, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")


class PredictionRecord(Base):
    __tablename__ = "prediction_records"
    __table_args__ = (
        CheckConstraint("length(trim(predicted_class_id)) > 0", name="ck_prediction_class_nonblank"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_prediction_confidence_range"),
        CheckConstraint("severity_percentage IS NULL OR (severity_percentage >= 0 AND severity_percentage <= 100)", name="ck_prediction_severity_percentage_range"),
        CheckConstraint("severity_category IS NULL OR severity_category IN ('Mild', 'Moderate', 'Severe')", name="ck_prediction_severity_category"),
        CheckConstraint("image_sha256 IS NULL OR length(image_sha256) = 64", name="ck_prediction_image_sha256_length"),
        Index("ix_prediction_records_created_at", "created_at"),
        Index("ix_prediction_records_class_created", "predicted_class_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    predicted_class_id: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(7, 6), nullable=False)
    severity_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    severity_percentage: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    severity_details: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    weather_context: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    recommendation_result: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    result_metadata: Mapped[dict | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    image_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_media_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    image_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    image_storage_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
