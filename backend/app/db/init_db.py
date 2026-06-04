"""数据库初始化脚本 — 应用启动时自动执行。"""

import logging
from sqlalchemy import text
from app.db.session import engine, AsyncSessionLocal
from app.db.models.workspace import ProjectSpace, ProjectSpaceActivity, ProjectSpaceMember, ProjectSpaceResource

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """初始化数据库：启用 pgvector 扩展，确保基础表存在。"""
    try:
        async with AsyncSessionLocal() as session:
            # 启用 pgvector 扩展
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            await session.commit()
            logger.info("✅ pgvector 和 uuid-ossp 扩展已启用")
        async with engine.begin() as conn:
            await conn.run_sync(ProjectSpace.metadata.create_all, tables=[
                ProjectSpace.__table__,
                ProjectSpaceMember.__table__,
                ProjectSpaceResource.__table__,
                ProjectSpaceActivity.__table__,
            ])
            logger.info("✅ 项目空间表已就绪")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
