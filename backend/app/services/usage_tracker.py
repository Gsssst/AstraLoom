"""Token 用量追踪服务。"""

import logging
import time
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta, timezone

from app.db.models.usage import TokenUsage
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


class UsageTracker:
    """Token 用量记录器。"""

    @staticmethod
    async def log_usage(
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        model: str = "deepseek-chat",
        endpoint: str = "chat/completions",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
    ):
        """记录一次 API 调用。"""
        # DeepSeek V4 价格估算 (CNY per 1M tokens)
        # 输入（缓存未命中）: ¥3, 缓存命中: ¥0.025, 输出: ¥6
        cost = (prompt_tokens / 1_000_000 * 3.0) + (completion_tokens / 1_000_000 * 6.0)

        try:
            async with AsyncSessionLocal() as session:
                record = TokenUsage(
                    user_id=user_id,
                    username=username,
                    model=model,
                    endpoint=endpoint,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost_estimate=round(cost, 6),
                )
                session.add(record)
                await session.commit()
        except Exception as e:
            logger.warning(f"Token 用量记录失败: {e}")

    @staticmethod
    async def get_user_stats(user_id: str) -> dict:
        """获取单个用户的用量统计。"""
        from uuid import UUID

        async with AsyncSessionLocal() as session:
            # 总计
            result = await session.execute(
                select(
                    func.sum(TokenUsage.total_tokens).label("total"),
                    func.sum(TokenUsage.prompt_tokens).label("prompt"),
                    func.sum(TokenUsage.completion_tokens).label("completion"),
                    func.count(TokenUsage.id).label("calls"),
                    func.sum(TokenUsage.cost_estimate).label("cost"),
                ).where(TokenUsage.user_id == UUID(user_id))
            )
            row = result.one()

            # 今日用量
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            result_today = await session.execute(
                select(func.sum(TokenUsage.total_tokens))
                .where(TokenUsage.user_id == UUID(user_id))
                .where(TokenUsage.called_at >= today)
            )
            today_tokens = result_today.scalar() or 0

            # 本月用量
            month_start = today.replace(day=1)
            result_month = await session.execute(
                select(func.sum(TokenUsage.total_tokens))
                .where(TokenUsage.user_id == UUID(user_id))
                .where(TokenUsage.called_at >= month_start)
            )
            month_tokens = result_month.scalar() or 0

            return {
                "total_tokens": int(row.total or 0),
                "total_prompt_tokens": int(row.prompt or 0),
                "total_completion_tokens": int(row.completion or 0),
                "total_calls": int(row.calls or 0),
                "estimated_cost": round(float(row.cost or 0), 4),
                "today_tokens": int(today_tokens),
                "month_tokens": int(month_tokens),
            }

    @staticmethod
    async def get_all_users_stats() -> list[dict]:
        """获取所有用户的用量统计。"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    TokenUsage.username,
                    TokenUsage.user_id,
                    func.sum(TokenUsage.total_tokens).label("total"),
                    func.count(TokenUsage.id).label("calls"),
                    func.sum(TokenUsage.cost_estimate).label("cost"),
                    func.max(TokenUsage.called_at).label("last_call"),
                )
                .where(TokenUsage.username.is_not(None))
                .group_by(TokenUsage.username, TokenUsage.user_id)
                .order_by(func.sum(TokenUsage.total_tokens).desc())
            )
            rows = result.all()

            return [
                {
                    "username": row.username or "anonymous",
                    "user_id": str(row.user_id) if row.user_id else None,
                    "total_tokens": int(row.total or 0),
                    "total_calls": int(row.calls or 0),
                    "estimated_cost": round(float(row.cost or 0), 4),
                    "last_call": row.last_call.isoformat() if row.last_call else None,
                }
                for row in rows
            ]

    @staticmethod
    async def get_recent_history(user_id: Optional[str] = None, limit: int = 50) -> list[dict]:
        """获取最近的使用记录。"""
        async with AsyncSessionLocal() as session:
            query = select(TokenUsage).order_by(TokenUsage.called_at.desc()).limit(limit)

            if user_id:
                from uuid import UUID
                query = query.where(TokenUsage.user_id == UUID(user_id))

            result = await session.execute(query)
            records = result.scalars().all()

            return [
                {
                    "id": str(r.id),
                    "username": r.username,
                    "model": r.model,
                    "endpoint": r.endpoint,
                    "total_tokens": r.total_tokens,
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "cost_estimate": r.cost_estimate,
                    "called_at": r.called_at.isoformat() if r.called_at else None,
                }
                for r in records
            ]
