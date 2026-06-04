"""项目空间 ORM 模型。"""

import uuid
from typing import Optional, List

from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class ProjectSpace(BaseModel):
    """统一科研项目空间。"""

    __tablename__ = "project_spaces"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    members: Mapped[List["ProjectSpaceMember"]] = relationship(
        "ProjectSpaceMember",
        back_populates="space",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    resources: Mapped[List["ProjectSpaceResource"]] = relationship(
        "ProjectSpaceResource",
        back_populates="space",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    activities: Mapped[List["ProjectSpaceActivity"]] = relationship(
        "ProjectSpaceActivity",
        back_populates="space",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_project_spaces_owner_status", "owner_id", "status"),
    )


class ProjectSpaceMember(BaseModel):
    """项目空间成员。"""

    __tablename__ = "project_space_members"

    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_spaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")

    space: Mapped["ProjectSpace"] = relationship("ProjectSpace", back_populates="members")

    __table_args__ = (
        UniqueConstraint("space_id", "user_id", name="uq_project_space_member"),
        Index("ix_project_space_members_user_role", "user_id", "role"),
    )


class ProjectSpaceResource(BaseModel):
    """项目空间显式绑定的资源。"""

    __tablename__ = "project_space_resources"

    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_spaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    added_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    space: Mapped["ProjectSpace"] = relationship("ProjectSpace", back_populates="resources")

    __table_args__ = (
        UniqueConstraint("space_id", "resource_type", "resource_id", name="uq_project_space_resource"),
        Index("ix_project_space_resources_space_type", "space_id", "resource_type"),
    )


class ProjectSpaceActivity(BaseModel):
    """项目空间活动日志。"""

    __tablename__ = "project_space_activities"

    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_spaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    space: Mapped["ProjectSpace"] = relationship("ProjectSpace", back_populates="activities")

    __table_args__ = (
        Index("ix_project_space_activities_space_created", "space_id", "created_at"),
        Index("ix_project_space_activities_actor_created", "actor_id", "created_at"),
    )
