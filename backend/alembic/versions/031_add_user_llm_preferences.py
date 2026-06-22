"""Add per-user LLM preferences.

Revision ID: 031
Revises: 030
"""
from alembic import op
import sqlalchemy as sa

revision: str = "031"
down_revision = "030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("llm_provider", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("llm_model", sa.String(120), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "llm_model")
    op.drop_column("users", "llm_provider")
