# ============================================================================
# Celery 异步任务队列配置
# 谁调用：workflow_tasks, routes
# ============================================================================
from celery import Celery
from app.core.config import settings
from app.utils.logger import logger

celery_app = Celery(
    "telecompass",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.workflow_tasks"]
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
)
logger.info(f"Celery 初始化完成，broker: {settings.REDIS_URL}")