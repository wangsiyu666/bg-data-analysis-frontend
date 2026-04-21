# ============================================================================
# 文件功能：执行计划表的 SQLAlchemy 模型，对应数据库表 execution_plans
# 谁调用它：execution_optimization.py：保存执行计划
# 它调用谁：Base
# ============================================================================
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from typing import List   # 添加这一行

class ExecutionPlan(Base):
    __tablename__ = "execution_plans"
    id = Column(String(50), primary_key=True, index=True)
    strategy_id = Column(String(50))
    audience_segment = Column(String(500))
    channel = Column(String(200))
    wave_count = Column(String(50), default="1")
    wave_interval_hours = Column(String(50))
    send_time_preference = Column(String(200))
    actual_conversion_rate = Column(String(50))
    actual_roi = Column(String(50))
    usage_count = Column(String(50), default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())