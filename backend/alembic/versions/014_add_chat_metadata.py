"""Add metadata_json to chat_sessions.

Revision ID: 014
Revises: 013
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chat_sessions", sa.Column("metadata_json", JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("chat_sessions", "metadata_json")
