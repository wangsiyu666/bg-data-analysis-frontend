# ============================================================================
# SQL 执行重试装饰器，最多重试5次，每次调用 LLM 修正 SQL
#Vanna 生成的 SQL 可能语法错误或字段名错误，导致查询失败。需要自动重试并修正。
# 谁调用：clickhouse_service 中的 execute_sql
# ============================================================================
import functools
from app.utils.logger import logger
from app.services.llm_service import call_llm_sync

def retry_on_sql_error(max_retries=5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(sql, *args, **kwargs):
            current_sql = sql
            for attempt in range(1, max_retries + 1):
                try:
                    result = func(current_sql, *args, **kwargs)
                    logger.info(f"SQL 执行成功 (尝试 {attempt}/{max_retries})")
                    return result
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"SQL 执行失败 (尝试 {attempt}/{max_retries}): {error_msg}\nSQL: {current_sql}")
                    if attempt == max_retries:
                        raise
                    correction_prompt = f"原始 SQL: {current_sql}\n错误信息: {error_msg}\n请修正 SQL 语句，只输出修正后的 SQL，不要有其他内容。"
                    corrected_sql = call_llm_sync(correction_prompt)
                    logger.info(f"LLM 修正后的 SQL: {corrected_sql}")
                    current_sql = corrected_sql
            return None
        return wrapper
    return decorator