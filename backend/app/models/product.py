# ============================================================================
# 文件功能：产品表的 SQLAlchemy 模型，对应数据库表 products
# 谁调用它：product_recommend.py：查询产品列表，推荐产品。
# strategy_generation.py：根据产品ID获取产品详情。
# execution_optimization.py：获取产品信息用于生成话术。
# 它调用谁：Base (database.py)
# ============================================================================
# ============================================================================
# 产品表模型，对应 PostgreSQL products 表
# ============================================================================
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from typing import List   # 添加这一行

class Product(Base):
    __tablename__ = "products"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(500))
    category = Column(String(200))
    sub_category = Column(String(200))
    price = Column(String(50))
    original_price = Column(String(50))
    discount_supported = Column(String(10), default="TRUE")
    description = Column(Text)
    target_user_type = Column(String(200))
    package_size = Column(String(200))
    valid_period = Column(String(200))
    applicable_scope = Column(String(500))
    is_active = Column(String(10), default="TRUE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())