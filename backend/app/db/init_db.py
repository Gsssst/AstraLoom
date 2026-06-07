"""数据库初始化脚本 — 应用启动时自动执行。"""

import logging
from sqlalchemy import text
from app.db.session import engine, AsyncSessionLocal
from app.db.models.paper import Folder, PaperFolderItem
from app.db.models.workspace import (
    ProjectSpace,
    ProjectSpaceActivity,
    ProjectSpaceIssue,
    ProjectSpaceIssueComment,
    ProjectSpaceMember,
    ProjectSpaceResource,
)

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """初始化数据库：启用 pgvector 扩展，确保基础表存在。"""
    try:
        async with AsyncSessionLocal() as session:
            # 启用 pgvector 扩展
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            await session.execute(text(
                "ALTER TABLE IF EXISTS digest_subscriptions "
                "ADD COLUMN IF NOT EXISTS send_hour INTEGER NOT NULL DEFAULT 8"
            ))
            await session.commit()
            logger.info("✅ pgvector、uuid-ossp 与兼容字段已就绪")
        async with engine.begin() as conn:
            await conn.run_sync(ProjectSpace.metadata.create_all, tables=[
                ProjectSpace.__table__,
                ProjectSpaceMember.__table__,
                ProjectSpaceResource.__table__,
                ProjectSpaceActivity.__table__,
                ProjectSpaceIssue.__table__,
                ProjectSpaceIssueComment.__table__,
                Folder.__table__,
                PaperFolderItem.__table__,
            ])
            logger.info("✅ 项目空间与论文分类表已就绪")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
