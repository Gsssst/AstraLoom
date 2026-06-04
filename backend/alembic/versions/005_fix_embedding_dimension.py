"""Fix embedding dimension from 1536 to 384 (sentence-transformers MiniLM).

Revision ID: 005
Revises: 004
Create Date: 2026-05-30
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 清空已有嵌入（如果有）
    op.execute("UPDATE papers SET embedding = NULL")
    # 删除旧索引
    op.execute("DROP INDEX IF EXISTS ix_papers_embedding_cosine")
    # 修改列类型
    op.alter_column("papers", "embedding", type_=Vector(384), postgresql_using="embedding::vector(384)")
    # 重新创建索引
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_papers_embedding_cosine "
        "ON papers USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"
    )


def downgrade() -> None:
    op.execute("UPDATE papers SET embedding = NULL")
    op.execute("DROP INDEX IF EXISTS ix_papers_embedding_cosine")
    op.alter_column("papers", "embedding", type_=Vector(1536), postgresql_using="embedding::vector(1536)")
