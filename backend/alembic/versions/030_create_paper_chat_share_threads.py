"""Create paper chat share discussion threads.

Revision ID: 030
Revises: 029
Create Date: 2026-06-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


revision = "030"
down_revision = "029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "paper_chat_share_threads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("paper_id", UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sender_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("metadata_json", JSON, nullable=True),
    )
    op.create_index("ix_paper_chat_share_threads_id", "paper_chat_share_threads", ["id"])
    op.create_index("ix_paper_chat_share_threads_paper_id", "paper_chat_share_threads", ["paper_id"])
    op.create_index("ix_paper_chat_share_threads_sender_id", "paper_chat_share_threads", ["sender_id"])

    op.create_table(
        "paper_chat_share_participants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("thread_id", UUID(as_uuid=True), sa.ForeignKey("paper_chat_share_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="recipient"),
        sa.Column("notification_id", UUID(as_uuid=True), sa.ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True),
        sa.UniqueConstraint("thread_id", "user_id", name="uq_paper_chat_share_participants_thread_user"),
    )
    op.create_index("ix_paper_chat_share_participants_id", "paper_chat_share_participants", ["id"])
    op.create_index("ix_paper_chat_share_participants_thread_id", "paper_chat_share_participants", ["thread_id"])
    op.create_index("ix_paper_chat_share_participants_user_id", "paper_chat_share_participants", ["user_id"])
    op.create_index("ix_paper_chat_share_participants_notification_id", "paper_chat_share_participants", ["notification_id"])
    op.create_index("ix_paper_chat_share_participants_user_thread", "paper_chat_share_participants", ["user_id", "thread_id"])

    op.create_table(
        "paper_chat_share_comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("thread_id", UUID(as_uuid=True), sa.ForeignKey("paper_chat_share_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
    )
    op.create_index("ix_paper_chat_share_comments_id", "paper_chat_share_comments", ["id"])
    op.create_index("ix_paper_chat_share_comments_thread_id", "paper_chat_share_comments", ["thread_id"])
    op.create_index("ix_paper_chat_share_comments_author_id", "paper_chat_share_comments", ["author_id"])
    op.create_index("ix_paper_chat_share_comments_thread_created", "paper_chat_share_comments", ["thread_id", "created_at"])

    op.create_table(
        "paper_chat_share_statuses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("thread_id", UUID(as_uuid=True), sa.ForeignKey("paper_chat_share_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.UniqueConstraint("thread_id", "user_id", name="uq_paper_chat_share_statuses_thread_user"),
    )
    op.create_index("ix_paper_chat_share_statuses_id", "paper_chat_share_statuses", ["id"])
    op.create_index("ix_paper_chat_share_statuses_thread_id", "paper_chat_share_statuses", ["thread_id"])
    op.create_index("ix_paper_chat_share_statuses_user_id", "paper_chat_share_statuses", ["user_id"])
    op.create_index("ix_paper_chat_share_statuses_user_status", "paper_chat_share_statuses", ["user_id", "status"])


def downgrade() -> None:
    op.drop_table("paper_chat_share_statuses")
    op.drop_table("paper_chat_share_comments")
    op.drop_table("paper_chat_share_participants")
    op.drop_table("paper_chat_share_threads")
