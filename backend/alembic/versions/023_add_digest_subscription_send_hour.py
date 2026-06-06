"""Add daily digest send hour.

Revision ID: 023
Revises: 022
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "digest_subscriptions",
        sa.Column("send_hour", sa.Integer(), nullable=False, server_default="8"),
    )
    op.alter_column("digest_subscriptions", "send_hour", server_default=None)


def downgrade() -> None:
    op.drop_column("digest_subscriptions", "send_hour")
