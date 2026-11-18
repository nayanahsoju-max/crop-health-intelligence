"""Create prediction history records.

Revision ID: 0001_prediction_history
Revises:
Create Date: 2026-09-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_prediction_history"
down_revision = None
branch_labels = None
depends_on = None

_json_document = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "prediction_records",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("predicted_class_id", sa.String(length=120), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=7, scale=6), nullable=False),
        sa.Column("severity_category", sa.String(length=20), nullable=True),
        sa.Column("severity_percentage", sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column("severity_details", _json_document, nullable=True),
        sa.Column("weather_context", _json_document, nullable=True),
        sa.Column("recommendation_result", _json_document, nullable=True),
        sa.Column("model_version", sa.String(length=120), nullable=True),
        sa.Column("image_filename", sa.String(length=255), nullable=True),
        sa.Column("image_media_type", sa.String(length=120), nullable=True),
        sa.Column("image_sha256", sa.String(length=64), nullable=True),
        sa.Column("image_storage_uri", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(trim(predicted_class_id)) > 0", name="ck_prediction_class_nonblank"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_prediction_confidence_range"),
        sa.CheckConstraint("severity_percentage IS NULL OR (severity_percentage >= 0 AND severity_percentage <= 100)", name="ck_prediction_severity_percentage_range"),
        sa.CheckConstraint("severity_category IS NULL OR severity_category IN ('Mild', 'Moderate', 'Severe')", name="ck_prediction_severity_category"),
        sa.CheckConstraint("image_sha256 IS NULL OR length(image_sha256) = 64", name="ck_prediction_image_sha256_length"),
    )
    op.create_index("ix_prediction_records_created_at", "prediction_records", ["created_at"])
    op.create_index("ix_prediction_records_class_created", "prediction_records", ["predicted_class_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_prediction_records_class_created", table_name="prediction_records")
    op.drop_index("ix_prediction_records_created_at", table_name="prediction_records")
    op.drop_table("prediction_records")
