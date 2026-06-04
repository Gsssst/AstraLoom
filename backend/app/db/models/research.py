"""研究方向相关 ORM 模型。"""

import uuid
from typing import List, Optional
from sqlalchemy import String, Text, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel


class ResearchProject(BaseModel):
    """研究方向项目。"""

    __tablename__ = "research_projects"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 研究方向关键词列表
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, completed, archived
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    paper_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)  # 手动添加的论文 ID

    ideas: Mapped[List["ResearchIdea"]] = relationship(
        back_populates="project", lazy="selectin", order_by="ResearchIdea.created_at.desc()"
    )
    idea_runs: Mapped[List["ResearchIdeaRun"]] = relationship(
        back_populates="project", lazy="selectin", order_by="ResearchIdeaRun.created_at.desc()"
    )


class ResearchIdeaRun(BaseModel):
    """一次可恢复的研究 Idea 工作台运行。"""

    __tablename__ = "research_idea_runs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, complete, failed
    stage: Mapped[str] = mapped_column(String(40), default="briefing")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    evidence_map: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    gap_map: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    candidate_pool: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    review_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["ResearchProject"] = relationship(back_populates="idea_runs")
    ideas: Mapped[List["ResearchIdea"]] = relationship(back_populates="generation_run", lazy="selectin")


class ResearchIdea(BaseModel):
    """研究 Idea 记录。"""

    __tablename__ = "research_ideas"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE")
    )
    generation_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_idea_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parent_idea_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_ideas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approach: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 技术方案
    novelty: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 创新点
    feasibility_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 可行性 1-10
    novelty_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 创新性 1-10
    referenced_papers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 引用的论文 ID 列表
    discussion_log: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 讨论记录
    generated_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 生成的代码
    hypothesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    review_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    experiment_plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    evolution_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, discussing, approved, implemented

    project: Mapped["ResearchProject"] = relationship(back_populates="ideas")
    generation_run: Mapped[Optional["ResearchIdeaRun"]] = relationship(back_populates="ideas")
