# ============================================================================
# 文件功能：话术库表的 SQLAlchemy 模型，对应数据库表 scripts
# 谁调用它：execution_optimization.py：保存生成的话术，查询历史话术
# 它调用谁：Base
# ============================================================================
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from typing import List   # 添加这一行

class Script(Base):
    __tablename__ = "scripts"
    id = Column(String(50), primary_key=True, index=True)
    content = Column(Text, nullable=False)
    scenario = Column(String(500))
    product_id = Column(String(50))
    strategy_id = Column(String(50))
    user_segment = Column(String(200))
    channel = Column(String(200))
    compliance_status = Column(String(50), default="approved")
    usage_count = Column(String(50), default="0")
    avg_ctr = Column(String(50), default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())