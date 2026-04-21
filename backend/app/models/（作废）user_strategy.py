# ============================================================================
# 运营用户清单表模型（ClickHouse）
#所有 ClickHouse 查询都通过 clickhouse_service.execute_sql 函数执行原生 SQL，没有使用 SQLAlchemy ORM
#所以此处无用
# ============================================================================
from sqlalchemy import Column, String, Float, Integer
from app.core.database import Base
from typing import List   # 添加这一行

class UserStrategy(Base):
    __tablename__ = "user_strategies"
    month_num = Column(String(6), primary_key=True)
    user_id = Column(String(50), primary_key=True)
    city_id = Column(String(20))
    yy_date = Column(String(14))
    strategy_id = Column(String(50))
    product_id = Column(String(50))
    plan_id = Column(String(50))
    script_id = Column(String(50))
    is_yy = Column(Integer)
    is_jt = Column(Integer)
    jt_date = Column(String(14))
    is_zh = Column(Integer)
    roi = Column(Float)
    zh_date = Column(String(14))
    extra_fields = Column(String)