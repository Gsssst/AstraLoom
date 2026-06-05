"""论文相关 ORM 模型。"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from typing import Any
from sqlalchemy import String, Integer, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.db.base import BaseModel, Base, TimestampMixin


class Paper(BaseModel):
    """论文模型 — 存储论文元数据和全文。"""

    __tablename__ = "papers"

    title: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    authors: Mapped[dict] = mapped_column(JSON, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, unique=True)
    arxiv_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="arxiv"
    )  # arxiv, semantic_scholar, manual, llm_recommend
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(384), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)  # AI 自动提取的关键词标签

    # 多对多关联分类
    categories: Mapped[List["Category"]] = relationship(
        secondary="paper_categories",
        back_populates="papers",
        lazy="selectin",
    )

    # 用户关联
    user_papers: Mapped[List["UserPaper"]] = relationship(
        back_populates="paper", lazy="selectin", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_papers_title_gin", "title"),
        Index("ix_papers_source", "source"),
    )

    def __repr__(self) -> str:
        return f"<Paper {self.title[:50]}... ({self.arxiv_id or self.doi})>"


class Category(BaseModel):
    """论文分类模型 — 支持多级分类树。"""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True
    )

    # 自引用 — 父子分类
    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side="Category.id", back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category", back_populates="parent", lazy="selectin"
    )

    # 多对多关联论文
    papers: Mapped[List["Paper"]] = relationship(
        secondary="paper_categories",
        back_populates="categories",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class PaperCategory(Base, TimestampMixin):
    """论文-分类关联模型（多对多）。"""

    __tablename__ = "paper_categories"

    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (
        UniqueConstraint("paper_id", "category_id", name="uq_paper_category"),
    )


class UserPaper(Base, TimestampMixin):
    """用户-论文关联模型（个人收藏、笔记）。"""

    __tablename__ = "user_papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    saved: Mapped[bool] = mapped_column(default=False)  # 是否收藏
    personal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 个人笔记
    read_status: Mapped[str] = mapped_column(String(20), default="unread")  # unread, reading, completed
    personal_tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)  # 个人标签
    paper_chat_history: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)  # 对话历史
    personal_annotations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)  # PDF 摘录/引用标注

    paper: Mapped["Paper"] = relationship(back_populates="user_papers")

    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uq_user_paper"),
    )

class Folder(Base, TimestampMixin):
    """论文文件夹（支持嵌套）。"""
    __tablename__ = "folders"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    parent: Mapped[Optional["Folder"]] = relationship("Folder", remote_side="Folder.id", back_populates="children")
    children: Mapped[list] = relationship("Folder", back_populates="parent", lazy="selectin")
    paper_items: Mapped[list["PaperFolderItem"]] = relationship(
        "PaperFolderItem",
        back_populates="folder",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PaperFolderItem(Base, TimestampMixin):
    """用户论文分类-论文关联。"""
    __tablename__ = "paper_folder_items"

    folder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"), primary_key=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )

    folder: Mapped["Folder"] = relationship(back_populates="paper_items")
    paper: Mapped["Paper"] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("folder_id", "paper_id", "user_id", name="uq_paper_folder_item"),
    )
