"""Database migration health helpers."""

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

MigrationHealthStatus = Literal["ok", "migration_required", "error"]


@dataclass(frozen=True)
class DatabaseMigrationStatus:
    """Current database migration state compared with the code revision head."""

    status: MigrationHealthStatus
    database: Literal["ok", "error"]
    current_revision: str | None
    head_revision: str | None
    is_current: bool
    detail: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def alembic_config_path() -> Path:
    return backend_root() / "alembic.ini"


def get_code_head_revision(config_path: Path | None = None) -> str | None:
    """Return the Alembic head revision known by the current code."""

    config = Config(str(config_path or alembic_config_path()))
    script = ScriptDirectory.from_config(config)
    heads = sorted(script.get_heads())
    return ",".join(heads) if heads else None


async def get_database_revision(db: AsyncSession) -> str | None:
    """Return the current database Alembic revision, or None when unversioned."""

    version_table = await db.execute(text("SELECT to_regclass('public.alembic_version')"))
    if version_table.scalar_one_or_none() is None:
        return None

    result = await db.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
    revisions = [row[0] for row in result.fetchall()]
    return ",".join(revisions) if revisions else None


async def get_database_migration_status(db: AsyncSession) -> DatabaseMigrationStatus:
    """Compare the connected database revision with the code revision head."""

    try:
        head_revision = get_code_head_revision()
    except Exception as exc:  # pragma: no cover - defensive startup diagnostic
        logger.exception("Failed to inspect Alembic code head")
        return DatabaseMigrationStatus(
            status="error",
            database="error",
            current_revision=None,
            head_revision=None,
            is_current=False,
            detail=f"Unable to inspect Alembic code head: {exc}",
        )

    try:
        current_revision = await get_database_revision(db)
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception("Failed to inspect database migration revision")
        return DatabaseMigrationStatus(
            status="error",
            database="error",
            current_revision=None,
            head_revision=head_revision,
            is_current=False,
            detail=f"Unable to inspect database revision: {exc}",
        )

    is_current = bool(head_revision) and current_revision == head_revision
    if is_current:
        return DatabaseMigrationStatus(
            status="ok",
            database="ok",
            current_revision=current_revision,
            head_revision=head_revision,
            is_current=True,
            detail=None,
        )

    if current_revision is None:
        detail = "Database is not versioned by Alembic; run alembic upgrade head."
    else:
        detail = "Database revision does not match code head; run alembic upgrade head."

    return DatabaseMigrationStatus(
        status="migration_required",
        database="ok",
        current_revision=current_revision,
        head_revision=head_revision,
        is_current=False,
        detail=detail,
    )


async def log_database_migration_status() -> DatabaseMigrationStatus:
    """Inspect and log migration status during application startup."""

    async with AsyncSessionLocal() as db:
        status = await get_database_migration_status(db)

    if status.status == "ok":
        logger.info("✅ 数据库迁移版本已是最新 (revision=%s)", status.current_revision)
    elif status.status == "migration_required":
        logger.warning(
            "⚠️ 数据库迁移版本不一致: current=%s head=%s。请运行 alembic upgrade head。",
            status.current_revision,
            status.head_revision,
        )
    else:
        logger.error("数据库迁移状态检查失败: %s", status.detail)

    return status
