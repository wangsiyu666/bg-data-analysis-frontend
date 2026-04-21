# ============================================================================
# 文件功能：客群分析智能体，基于 text-to-sql 获取用户特征组合
# 谁调用它：simple_agents, graph (路由)
# 它调用谁：vanna_service, clickhouse_service, logger
# ============================================================================
from app.services.vanna_service import generate_sql
from app.services.clickhouse_service import execute_sql
from app.utils.logger import logger
from typing import List   # 添加这一行

def analyze_audience(question: str, user_id: str = "system") -> dict:
    """
    根据自然语言问题分析客群特征，返回 SQL 结果和特征组合描述
    参数:
        question: 自然语言问题
        user_id: 操作用户标识（用于日志）
    返回:
        包含 sql, result, features, suggested_condition 的字典
    """
    logger.info(f"[客群分析] 用户 {user_id}, 问题: {question}")
    sql = generate_sql(question)
    result = execute_sql(sql)
    features = result.get("columns", [])
    logger.info(f"分析完成，特征字段: {features}")
    return {
        "sql": sql,
        "result": result,
        "features": features,
        "suggested_condition": question  # 可直接用于客群圈选
    }