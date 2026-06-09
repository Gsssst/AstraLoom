"""Add shared paper importance marker.

Revision ID: 028
Revises: 027
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("papers", sa.Column("importance_label", sa.String(length=20), nullable=True))
    op.add_column("papers", sa.Column("importance_note", sa.String(length=500), nullable=True))
    op.create_index("ix_papers_importance_label", "papers", ["importance_label"])


def downgrade() -> None:
    op.drop_index("ix_papers_importance_label", table_name="papers")
    op.drop_column("papers", "importance_note")
    op.drop_column("papers", "importance_label")
