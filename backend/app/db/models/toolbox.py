"""Research toolbox ORM models."""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class ResearchTool(BaseModel):
    """Reusable research tool, method, dataset, metric, or protocol."""

    __tablename__ = "research_tools"

    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False, default="algorithm", index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    use_cases: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    maturity: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown", index=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    paper_links: Mapped[list["ResearchToolPaper"]] = relationship(
        back_populates="tool",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_research_tools_name_kind", "name", "kind"),
    )


class ResearchToolPaper(BaseModel):
    """Paper evidence linked to a reusable research tool."""

    __tablename__ = "research_tool_papers"

    tool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_tools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation: Mapped[str] = mapped_column(String(40), nullable=False, default="used", index=True)
    evidence_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    tool: Mapped["ResearchTool"] = relationship(back_populates="paper_links")
    paper = relationship("Paper", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tool_id", "paper_id", name="uq_research_tool_paper"),
        Index("ix_research_tool_papers_tool_relation", "tool_id", "relation"),
    )
