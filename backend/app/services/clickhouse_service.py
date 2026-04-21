# ============================================================================
# ClickHouse 数据库操作，执行 SQL 并返回结果，同时带有自动重试机制（最多5次，每次失败会调用 LLM 修正 SQL）
# 谁调用：audience_analysis, audience_selection, evaluation 等
# ============================================================================
from clickhouse_driver import Client
from app.core.config import settings
from app.utils.logger import logger
from app.utils.sql_retry import retry_on_sql_error
from typing import List   # 添加这一行

client = Client(
    host=settings.CLICKHOUSE_HOST,
    port=settings.CLICKHOUSE_PORT,
    user="default",
    password=""
)

@retry_on_sql_error(max_retries=5)
def execute_sql(sql: str) -> dict:
    """
    执行 SQL 并返回列名和数据
    参数: sql: SQL 语句
    返回: {"columns": [列名], "data": [[值]]}
    """
    logger.info(f"执行 ClickHouse SQL: {sql[:200]}...")
    columns, data = client.execute(sql, with_column_types=True)
    column_names = [col[0] for col in columns]
    logger.info(f"查询成功，返回 {len(data)} 行，列: {column_names}")
    return {"columns": column_names, "data": data}