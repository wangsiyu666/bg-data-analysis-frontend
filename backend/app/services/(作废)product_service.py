# ============================================================================
# 文件作用：产品库服务，从 PostgreSQL 中获取产品信息
# 能力：提供产品列表查询，供策略生成时选择关联产品
# 后续使用场景：策略生成智能体中调用，获取可选产品列表
# ============================================================================
from sqlalchemy.orm import Session
from app.models.product import Product
from app.utils.logger import logger
from typing import List   # 添加这一行

def get_active_products(db: Session) -> list:
    """获取所有上架的产品"""
    # query 方法：查询 Product 表，filter 过滤 is_active == True，all() 返回所有结果
    products = db.query(Product).filter(Product.is_active == True).all()
    logger.info(f"获取到 {len(products)} 个产品")
    return products

def get_product_by_id(db: Session, product_id: int) -> Product:
    """根据 ID 获取产品"""
    return db.query(Product).filter(Product.id == product_id).first()