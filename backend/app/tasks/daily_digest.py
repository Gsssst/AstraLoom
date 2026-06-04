"""每日 arXiv 摘要推送定时任务。"""

import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.db.models.notification import DigestSubscription
from app.services.digest_service import DigestService

logger = logging.getLogger(__name__)


@celery_app.task(name="daily_arxiv_digest")
def daily_arxiv_digest():
    """每日执行：为所有订阅用户抓取 arXiv 并生成通知。"""
    import asyncio
    return asyncio.run(_run_digest())


async def _run_digest():
    async with AsyncSessionLocal() as session:
        # 获取所有启用了推送的订阅
        result = await session.execute(
            select(DigestSubscription).where(
                DigestSubscription.push_enabled == True
            )
        )
        subscriptions = result.scalars().all()

        if not subscriptions:
            logger.info("无活跃订阅，跳过每日推送")
            return

        digest_service = DigestService(session)
        now = datetime.now(timezone.utc)
        total_notified = 0

        for sub in subscriptions:
            kws = sub.keywords or []
            if not kws:
                continue

            try:
                delivery = await digest_service.dispatch_in_app_digest(
                    user_id=sub.user_id,
                    keywords=kws,
                )
                if not delivery["delivered"]:
                    continue
                sub.last_sent_at = now
                total_notified += 1

            except Exception as e:
                logger.error(f"用户 {sub.user_id} 推送失败: {e}")
                continue

        await session.commit()
        logger.info(f"每日推送完成: {total_notified}/{len(subscriptions)} 位用户收到通知")
        return {"notified": total_notified, "subscriptions": len(subscriptions)}
