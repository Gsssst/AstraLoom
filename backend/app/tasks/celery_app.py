"""Celery 异步任务队列配置。"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "auto_research",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.paper_tasks",
        "app.tasks.daily_digest",
    ],
)

# 序列化配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 单个任务最长 1 小时
    task_soft_time_limit=3000,  # 软限制 50 分钟
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    beat_schedule={
        "daily-arxiv-digest": {
            "task": "daily_arxiv_digest",
            "schedule": crontab(hour=8, minute=0),
            "options": {"expires": 3600},
        },
    },
)

# 自动发现任务
celery_app.autodiscover_tasks(["app.tasks"])
