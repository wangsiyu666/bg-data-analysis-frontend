# ============================================================================
# 文件功能：策略表的 SQLAlchemy 模型，对应数据库表 strategies
# 谁调用它：strategy_generation.py：保存新策略，查询历史策略。
# execution_optimization.py：获取策略详情。
# evaluation.py：根据策略ID评估效果。
# 它调用谁：Base
#product_ids 存储为逗号分隔的字符串，使用时需要 split(',') 解析。
# ============================================================================
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from typing import List   # 添加这一行

class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(500))
    category = Column(String(200))
    description = Column(Text)
    product_ids = Column(String(500))
    conditions = Column(Text)
    channel_preference = Column(String(200))
    discount_ratio = Column(String(50))
    avg_conversion_rate = Column(String(50), default="0")
    avg_roi = Column(String(50), default="0")
    avg_click_rate = Column(String(50), default="0")
    sample_count = Column(String(50), default="0")
    is_active = Column(String(10), default="TRUE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())