#!/usr/bin/env python
# ============================================================================
# 文件作用：Vanna 训练脚本，用于初始化训练和后续增量训练
# 使用方法：python -m app.services.vanna_trainer --train-ddl --train-doc
# 能力：可单独运行，增加训练数据，提升 SQL 生成准确率
# ============================================================================
import argparse
from app.services.vanna_service import vn, init_vanna
from app.utils.logger import logger
from typing import List   # 添加这一行

# 额外的训练素材（与 vanna_service.py 中的训练内容互补，用于增量训练）
EXTRA_DDL = [
    """
    CREATE TABLE user_behavior (
        user_id String,
        event_date Date,
        traffic_mb Int64,
        arpu Decimal(10,2),
        flow_overflow Int8,
        last_active_date Date
    ) ENGINE = MergeTree ORDER BY (event_date);
    """,
    """
    CREATE TABLE user_profile (
        user_id String,
        age Int8,
        city String,
        phone String,
        id_card String,
        user_level String
    ) ENGINE = MergeTree ORDER BY (user_id);
    """
]

EXTRA_DOCS = [
    "流量超套用户：指当月已用流量超过套餐内包含流量的用户。",
    "ARPU：Average Revenue Per User，每用户平均收入，单位元。",
    "挽留策略：针对可能流失的用户推送优惠。",
    "user_id：用户唯一标识，脱敏显示。"
]

def train_ddl():
    """训练 DDL（数据定义语言）"""
    for ddl in EXTRA_DDL:
        vn.train(ddl=ddl)
        logger.info(f"训练DDL: {ddl[:50]}...")

def train_documentation():
    """训练文档（业务术语解释）"""
    for doc in EXTRA_DOCS:
        vn.train(documentation=doc)
        logger.info(f"训练文档: {doc[:50]}...")

def train_sql(sql: str, question: str):
    """训练 SQL 样例（问题-SQL 对）"""
    vn.train(question=question, sql=sql)
    logger.info(f"训练SQL: {question} -> {sql[:100]}")

def main():
    parser = argparse.ArgumentParser(description="Vanna 训练工具")
    parser.add_argument("--train-ddl", action="store_true", help="训练 DDL")
    parser.add_argument("--train-doc", action="store_true", help="训练文档")
    parser.add_argument("--sql-question", type=str, help="问题和SQL，格式: '问题|SQL'")
    args = parser.parse_args()
    
    init_vanna()
    if args.train_ddl:
        train_ddl()
    if args.train_doc:
        train_documentation()
    if args.sql_question:
        q, sql = args.sql_question.split("|", 1)
        train_sql(sql, q)
    logger.info("训练完成")

if __name__ == "__main__":
    main()