"""通知和订阅模型。"""

import uuid
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, func, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, BaseModel


class DigestSubscription(Base, TimestampMixin):
    """用户 arXiv 推送订阅配置。"""

    __tablename__ = "digest_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    frequency: Mapped[str] = mapped_column(String(20), default="daily")  # daily, weekly
    send_hour: Mapped[int] = mapped_column(default=8)
    last_sent_at: Mapped[Optional[str]] = mapped_column(DateTime(timezone=True), nullable=True)


class Notification(Base, TimestampMixin):
    """系统通知。"""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="system")  # digest, system, share
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class PaperChatShareThread(BaseModel):
    """论文 AI 精读分享讨论串。"""

    __tablename__ = "paper_chat_share_threads"

    paper_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    participants: Mapped[List["PaperChatShareParticipant"]] = relationship(
        "PaperChatShareParticipant",
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    comments: Mapped[List["PaperChatShareComment"]] = relationship(
        "PaperChatShareComment",
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    statuses: Mapped[List["PaperChatShareStatus"]] = relationship(
        "PaperChatShareStatus",
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PaperChatShareParticipant(BaseModel):
    """论文 AI 精读分享参与者。"""

    __tablename__ = "paper_chat_share_participants"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_chat_share_threads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="recipient")
    notification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True, index=True
    )

    thread: Mapped["PaperChatShareThread"] = relationship("PaperChatShareThread", back_populates="participants")

    __table_args__ = (
        UniqueConstraint("thread_id", "user_id", name="uq_paper_chat_share_participants_thread_user"),
        Index("ix_paper_chat_share_participants_user_thread", "user_id", "thread_id"),
    )


class PaperChatShareComment(BaseModel):
    """论文 AI 精读分享评论。"""

    __tablename__ = "paper_chat_share_comments"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_chat_share_threads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    thread: Mapped["PaperChatShareThread"] = relationship("PaperChatShareThread", back_populates="comments")

    __table_args__ = (
        Index("ix_paper_chat_share_comments_thread_created", "thread_id", "created_at"),
    )


class PaperChatShareStatus(BaseModel):
    """论文 AI 精读分享的用户侧处理状态。"""

    __tablename__ = "paper_chat_share_statuses"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_chat_share_threads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)

    thread: Mapped["PaperChatShareThread"] = relationship("PaperChatShareThread", back_populates="statuses")

    __table_args__ = (
        UniqueConstraint("thread_id", "user_id", name="uq_paper_chat_share_statuses_thread_user"),
        Index("ix_paper_chat_share_statuses_user_status", "user_id", "status"),
    )
