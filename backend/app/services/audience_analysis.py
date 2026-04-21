# ============================================================================
# 文件功能：客群分析智能体，提供自然语言转SQL、执行SQL、保存客群、多维分析
# 谁调用：simple_agents, 路由
# ============================================================================
import re
import time
import uuid
from typing import List
from app.services.vanna_service import generate_sql
from app.services.clickhouse_service import execute_sql, client as ch_client
from app.utils.logger import logger

def nl2sql(question: str) -> dict:
    """自然语言转SQL"""
    logger.info(f"NL2SQL: {question}")
    sql = generate_sql(question)
    return {"sql": sql}

def execute_analysis(sql: str) -> dict:
    """执行SQL并返回结果"""
    logger.info(f"执行SQL: {sql[:200]}...")
    result = execute_sql(sql)
    return {
        "columns": result["columns"],
        "data": result["data"],
        "total": len(result["data"])
    }

def save_audience(name: str, condition_sql: str) -> dict:
    """
    保存客群：将满足条件的用户ID列表写入 ClickHouse 的 audience_groups 表
    支持两种输入：
      1. SQL 中已包含 user_id 列，直接执行提取 user_id
      2. SQL 为聚合统计（如 COUNT(*), GROUP BY），自动改写为 SELECT user_id FROM user_behavior WHERE ... 后提取 user_id
    参数:
        name: 客群名称
        condition_sql: 原始 SQL 语句
    返回:
        包含 status 和 audience_id 的字典
    """
    logger.info(f"保存客群: {name}, 原始SQL: {condition_sql[:200]}...")

    # 1. 生成唯一客群ID
    audience_id = f"aud_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    # 2. 判断 SQL 是否已经包含 user_id 列（简单文本匹配，忽略大小写）
    sql_upper = condition_sql.upper()
    has_user_id = re.search(r'\bSELECT\b.*\bUSER_ID\b', sql_upper) is not None

    user_ids = []
    if has_user_id:
        # 情况1：SQL 已包含 user_id，直接执行
        logger.info("SQL 已包含 user_id，直接执行")
        try:
            result = execute_sql(condition_sql)
            columns = result.get("columns", [])
            # 查找 user_id 列的位置
            try:
                uid_idx = columns.index("user_id")
            except ValueError:
                uid_idx = next((i for i, c in enumerate(columns) if c.lower() == "user_id"), None)
                if uid_idx is None:
                    return {"status": "error", "message": "SQL 返回结果中未找到 user_id 列"}
            for row in result.get("data", []):
                if len(row) > uid_idx:
                    user_ids.append(str(row[uid_idx]))
        except Exception as e:
            logger.error(f"执行 SQL 失败: {e}", exc_info=True)
            return {"status": "error", "message": f"执行 SQL 失败: {str(e)}"}
    else:
        # 情况2：SQL 不包含 user_id，尝试改写为 SELECT user_id FROM user_behavior WHERE ...
        logger.info("SQL 不包含 user_id，尝试改写")
        # 提取 FROM 表名和 WHERE 条件（假设 SQL 格式为 SELECT ... FROM user_behavior WHERE ...）
        # 正则匹配：FROM\s+(\w+)\s+WHERE\s+(.*)$
        match = re.search(r'FROM\s+(\w+)\s+WHERE\s+(.*)$', condition_sql, re.IGNORECASE)
        if not match:
            return {"status": "error", "message": "无法解析 SQL，请确保 SQL 包含 FROM user_behavior WHERE 条件，或直接提供包含 user_id 的查询"}
        table_name = match.group(1)
        where_clause = match.group(2)
        new_sql = f"SELECT user_id FROM {table_name} WHERE {where_clause}"
        logger.info(f"改写后的 SQL: {new_sql}")
        try:
            result = execute_sql(new_sql)
            user_ids = [str(row[0]) for row in result.get("data", [])]
        except Exception as e:
            logger.error(f"执行改写后的 SQL 失败: {e}", exc_info=True)
            return {"status": "error", "message": f"执行改写后的 SQL 失败: {str(e)}"}

    if not user_ids:
        logger.warning("未获取到任何 user_id，客群为空")
        return {"status": "error", "message": "未找到任何用户，请检查条件"}

    # 3. 批量插入 ClickHouse
    try:
        batch_size = 1000
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i+batch_size]
            for uid in batch:
                ch_client.execute(
                    "INSERT INTO audience_groups (audience_id, name, condition_sql, user_id, created_at) VALUES (%s, %s, %s, %s, now())",
                    (audience_id, name, condition_sql, uid)
                )
        logger.info(f"客群保存成功，audience_id={audience_id}, 用户数={len(user_ids)}")
        return {"status": "success", "audience_id": audience_id}
    except Exception as e:
        logger.error(f"插入 audience_groups 失败: {e}", exc_info=True)
        return {"status": "error", "message": f"数据库写入失败: {str(e)}"}

def multidim_analysis(base_sql: str) -> dict:
    """
    多维分析：根据基础SQL中的WHERE条件，从 ClickHouse 实时计算生命周期、高/低价值分布、雷达图、诊断表格。
    参数 base_sql: 形如 "FROM user_behavior WHERE arpu > 100"（也可以只有 "FROM user_behavior"，此时无WHERE条件）
    返回 PRD 要求的数据结构
    """
    logger.info(f"多维分析，基础SQL: {base_sql}")

    # 1. 提取 WHERE 条件（如果存在）
    # 匹配 "WHERE" 后面的部分，直到字符串结束
    match = re.search(r'WHERE\s+(.*)$', base_sql, re.IGNORECASE)
    if match:
        where_clause = match.group(1).strip()
    else:
        where_clause = "1=1"  # 无 WHERE 条件时查询全部
    logger.debug(f"提取的 WHERE 条件: {where_clause}")

    # 2. 生命周期卡片（按 user_online 分段统计用户数）
    lifecycle_sql = f"""
        SELECT
            countIf(user_online < 6) AS 入网期,
            countIf(user_online >= 6 AND user_online < 18) AS 成长期,
            countIf(user_online >= 18 AND user_online < 36) AS 成熟期,
            countIf(user_online >= 36 AND user_online < 60) AS 异动期,
            countIf(user_online >= 60) AS 离网期
        FROM user_behavior
        WHERE {where_clause}
    """
    lifecycle_result = execute_sql(lifecycle_sql)
    # 假设返回一行，五个值
    row = lifecycle_result['data'][0] if lifecycle_result['data'] else [0,0,0,0,0]
    lifecycle = [
        {"stage": "入网期", "count": row[0], "condition": "user_online < 6"},
        {"stage": "成长期", "count": row[1], "condition": "user_online < 18"},
        {"stage": "成熟期", "count": row[2], "condition": "user_online < 36"},
        {"stage": "异动期", "count": row[3], "condition": "user_online < 60"},
        {"stage": "离网期", "count": row[4], "condition": "user_online >= 60"},
    ]
    logger.info(f"生命周期卡片数据: {lifecycle}")

    # 3. 高/低价值分布（按生命周期阶段，高价值：arpu > 80，低价值：arpu <= 80）
    # 阈值 80 可以根据业务调整，建议作为参数或配置
    high_low_sql = f"""
        SELECT
            CASE
                WHEN user_online < 6 THEN '入网期'
                WHEN user_online >= 6 AND user_online < 18 THEN '成长期'
                WHEN user_online >= 18 AND user_online < 36 THEN '成熟期'
                WHEN user_online >= 36 AND user_online < 60 THEN '异动期'
                ELSE '离网期'
            END AS stage,
            countIf(arpu > 80) AS high,
            countIf(arpu <= 80) AS low
        FROM user_behavior
        WHERE {where_clause}
        GROUP BY stage
    """
    high_low_result = execute_sql(high_low_sql)
    # 转换为字典 {"入网期": {"high": 345, "low": 234}, ...}
    high_low_dist = {}
    for row in high_low_result['data']:
        stage = row[0]
        high_low_dist[stage] = {"high": row[1], "low": row[2]}
    # 确保所有生命周期阶段都有值（若某些阶段无数据，补0）
    stages = ["入网期", "成长期", "成熟期", "异动期", "离网期"]
    for s in stages:
        if s not in high_low_dist:
            high_low_dist[s] = {"high": 0, "low": 0}
    logger.info(f"高/低价值分布: {high_low_dist}")

    # 4. 雷达图（六个维度：粘性、价值、竞抢、感知、活跃、传播）
    # 假设字段映射：
    # 粘性 = is_rhtc (是否融合套餐) 或类似字段，这里用 is_rhtc 求和
    # 价值 = arpu 平均值
    # 竞抢 = is_ywsk (是否异网双卡) 求和
    # 感知 = is_ts (投诉次数>0) 求和
    # 活跃 = active_mark 求和
    # 传播 = call_opp_counts1 (交往圈人数) 平均值
    # 如果实际表中字段不同，请根据实际情况修改
    radar_sql = f"""
        SELECT
            sum(is_rhtc) AS 粘性,
            avg(arpu) AS 价值,
            sum(is_ywsk) AS 竞抢,
            sum(is_ts) AS 感知,
            sum(active_mark) AS 活跃,
            avg(call_opp_counts1) AS 传播
        FROM user_behavior
        WHERE {where_clause}
    """
    radar_result = execute_sql(radar_sql)
    if radar_result['data']:
        radar_row = radar_result['data'][0]
        radar_data = {
            "粘性": radar_row[0],
            "价值": round(radar_row[1], 2),
            "竞抢": radar_row[2],
            "感知": radar_row[3],
            "活跃": radar_row[4],
            "传播": round(radar_row[5], 2)
        }
    else:
        radar_data = {"粘性": 0, "价值": 0, "竞抢": 0, "感知": 0, "活跃": 0, "传播": 0}
    logger.info(f"雷达图数据: {radar_data}")

    # 5. 诊断表格（按生命周期阶段展示各维度数值）
    # 类似高/低价值分布，但需要多个维度的聚合
    diagnosis_sql = f"""
        SELECT
            CASE
                WHEN user_online < 6 THEN '入网期'
                WHEN user_online >= 6 AND user_online < 18 THEN '成长期'
                WHEN user_online >= 18 AND user_online < 36 THEN '成熟期'
                WHEN user_online >= 36 AND user_online < 60 THEN '异动期'
                ELSE '离网期'
            END AS stage,
            sum(is_rhtc) AS 粘性,
            avg(arpu) AS 价值,
            sum(is_ywsk) AS 竞抢,
            sum(is_ts) AS 感知,
            sum(active_mark) AS 活跃,
            avg(call_opp_counts1) AS 传播
        FROM user_behavior
        WHERE {where_clause}
        GROUP BY stage
        ORDER BY stage
    """
    diagnosis_result = execute_sql(diagnosis_sql)
    diagnosis_table = []
    for row in diagnosis_result['data']:
        diagnosis_table.append({
            "lifecycle": row[0],
            "粘性": row[1],
            "价值": round(row[2], 2),
            "竞抢": row[3],
            "感知": row[4],
            "活跃": row[5],
            "传播": round(row[6], 2)
        })
    # 确保所有阶段都有数据
    stages_order = ["入网期", "成长期", "成熟期", "异动期", "离网期"]
    existing_stages = [item["lifecycle"] for item in diagnosis_table]
    for s in stages_order:
        if s not in existing_stages:
            diagnosis_table.append({
                "lifecycle": s,
                "粘性": 0,
                "价值": 0,
                "竞抢": 0,
                "感知": 0,
                "活跃": 0,
                "传播": 0
            })
    # 按生命周期顺序排序
    diagnosis_table.sort(key=lambda x: stages_order.index(x["lifecycle"]))
    logger.info(f"诊断表格行数: {len(diagnosis_table)}")

    return {
        "lifecycle": lifecycle,
        "high_low_dist": high_low_dist,
        "radar": radar_data,
        "diagnosis_table": diagnosis_table
    }