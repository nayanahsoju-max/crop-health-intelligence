"""Store full inference workflow metadata.

Revision ID: 0002_prediction_result_metadata
Revises: 0001_prediction_history
Create Date: 2026-09-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_prediction_result_metadata"
down_revision = "0001_prediction_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("prediction_records", sa.Column(
        "result_metadata", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True
    ))


def downgrade() -> None:
    op.drop_column("prediction_records", "result_metadata")
