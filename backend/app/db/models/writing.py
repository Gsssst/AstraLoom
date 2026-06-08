"""写作项目管理 ORM 模型。"""

import uuid
from typing import Optional, List
from sqlalchemy import String, Integer, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel


class WritingProject(BaseModel):
    """写作项目 — 管理整篇论文的写作过程。"""

    __tablename__ = "writing_projects"

    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="blank"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    sections: Mapped[List["WritingSection"]] = relationship(
        "WritingSection", back_populates="project",
        cascade="all, delete-orphan", order_by="WritingSection.order",
    )

    __table_args__ = (
        Index("ix_writing_projects_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<WritingProject {self.title} ({self.template_type}) status={self.status}>"


class WritingSection(BaseModel):
    """写作章节 — 论文的单个章节。"""

    __tablename__ = "writing_sections"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("writing_projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    project: Mapped["WritingProject"] = relationship(
        "WritingProject", back_populates="sections"
    )
    polish_versions: Mapped[List["PolishVersion"]] = relationship(
        "PolishVersion", back_populates="section",
        cascade="all, delete-orphan", order_by="PolishVersion.version_number",
    )

    __table_args__ = (
        Index("ix_writing_sections_project_order", "project_id", "order"),
    )

    def __repr__(self) -> str:
        return f"<WritingSection {self.title} (order={self.order}) status={self.status}>"


class PolishVersion(BaseModel):
    """润色版本 — 记录每次润色的原文、结果和 diff。"""

    __tablename__ = "polish_versions"

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("writing_sections.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    polished_text: Mapped[str] = mapped_column(Text, nullable=False)
    diff_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    user_actions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    section: Mapped["WritingSection"] = relationship(
        "WritingSection", back_populates="polish_versions"
    )

    __table_args__ = (
        Index("ix_polish_versions_section_version", "section_id", "version_number"),
    )

    def __repr__(self) -> str:
        return f"<PolishVersion v{self.version_number} for section={str(self.section_id)[:8]}>"
