"""每日 arXiv 摘要推送定时任务。"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal, engine
from app.db.models.notification import DigestSubscription
from app.services.digest_service import DigestService

logger = logging.getLogger(__name__)
BEIJING_TZ = ZoneInfo("Asia/Shanghai")


@celery_app.task(name="daily_arxiv_digest")
def daily_arxiv_digest():
    """每日执行：为所有订阅用户抓取 arXiv 并生成通知。"""
    import asyncio
    return asyncio.run(_run_digest_task())


async def _run_digest_task():
    try:
        return await _run_digest()
    finally:
        await engine.dispose()


def _sent_on_beijing_day(last_sent_at, current_day) -> bool:
    if not last_sent_at:
        return False
    if last_sent_at.tzinfo is None:
        sent = last_sent_at.replace(tzinfo=BEIJING_TZ)
    else:
        sent = last_sent_at.astimezone(BEIJING_TZ)
    return sent.date() == current_day


async def _run_digest(now: datetime | None = None):
    now_bj = (now.astimezone(BEIJING_TZ) if now and now.tzinfo else (now or datetime.now(BEIJING_TZ))).replace(tzinfo=BEIJING_TZ)
    async with AsyncSessionLocal() as session:
        # 获取所有启用了推送的订阅
        result = await session.execute(
            select(DigestSubscription).where(
                DigestSubscription.push_enabled == True,
                DigestSubscription.frequency == "daily",
            )
        )
        subscriptions = result.scalars().all()

        if not subscriptions:
            logger.info("无活跃订阅，跳过每日推送")
            return

        digest_service = DigestService(session)
        total_notified = 0
        total_due = 0

        for sub in subscriptions:
            kws = sub.keywords or []
            if not kws:
                continue
            if int(getattr(sub, "send_hour", 8) or 8) != now_bj.hour:
                continue
            if _sent_on_beijing_day(sub.last_sent_at, now_bj.date()):
                continue
            total_due += 1

            try:
                delivery = await digest_service.dispatch_in_app_digest(
                    user_id=sub.user_id,
                    keywords=kws,
                    notify_on_empty=True,
                )
                if not delivery["delivered"]:
                    continue
                sub.last_sent_at = now_bj
                total_notified += 1

            except Exception as e:
                logger.error(f"用户 {sub.user_id} 推送失败: {e}")
                continue

        await session.commit()
        logger.info(f"每日推送完成: {total_notified}/{total_due} 位到点用户收到通知，活跃订阅 {len(subscriptions)}")
        return {"notified": total_notified, "due": total_due, "subscriptions": len(subscriptions), "hour": now_bj.hour}
