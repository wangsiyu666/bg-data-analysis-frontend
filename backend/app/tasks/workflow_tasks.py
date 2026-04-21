# ============================================================================
# Celery 任务定义，执行用户请求
# 谁调用：routes.py 中的 /unified 接口（可选），此处主要用于异步长任务
# ============================================================================
from celery import Task
from app.tasks.celery_app import celery_app
from app.agents.graph import route_user_request
from app.utils.logger import logger

class RouteTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"任务 {task_id} 失败: {exc}", exc_info=True)

@celery_app.task(base=RouteTask, bind=True)
def process_user_request(self, action: str, params: dict) -> dict:
    """
    异步处理用户请求
    参数: action: 操作类型, params: 参数字典
    返回: 处理结果
    """
    logger.info(f"异步任务开始: action={action}, params={params}")
    try:
        result = route_user_request(action, params)
        logger.info("异步任务完成")
        return result
    except Exception as e:
        logger.error(f"异步任务异常: {e}", exc_info=True)
        raise