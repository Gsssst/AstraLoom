"""Add embedding column to papers table.

Revision ID: 004
Revises: 003
Create Date: 2026-05-30
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("papers", sa.Column("embedding", Vector(384), nullable=True))
    # 创建向量索引（用于加速相似度搜索）
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_papers_embedding_cosine "
        "ON papers USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_index("ix_papers_embedding_cosine", table_name="papers")
    op.drop_column("papers", "embedding")
