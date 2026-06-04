"""对话会话模型。"""

import uuid
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class ChatSession(Base, TimestampMixin):
    """用户对话会话。"""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False, default="新对话")
    rag_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="session", lazy="selectin",
        order_by="ChatMessage.created_at", cascade="all, delete-orphan"
    )


class ChatMessage(Base, TimestampMixin):
    """对话消息。"""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    references: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
