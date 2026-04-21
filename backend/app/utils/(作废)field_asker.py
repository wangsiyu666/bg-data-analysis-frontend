# ============================================================================
# 文件作用：客群字段追问逻辑，当用户未指定返回字段时，自动推荐常用字段
# 能力：提升用户体验，避免因缺少字段而返回空数据
# 后续使用场景：在客群圈选服务中，当 fields 参数为空时调用
# ============================================================================
from app.utils.logger import logger

def ask_user_for_fields(condition: str, available_fields: list) -> list:
    """
    模拟询问用户需要返回哪些字段。
    实际生产中可通过 WebSocket 与前端交互，这里简化：返回默认字段列表。
    
    参数:
        condition: 圈选条件（自然语言）
        available_fields: 所有可用的字段列表（从元数据获取）
    
    返回:
        用户选择的字段列表（当前版本自动推荐）
    """
    logger.info(f"客群条件: {condition}, 可用字段: {available_fields}")
    # 根据业务经验推荐常用字段（这些字段通常存在于 user_behavior 和 user_profile 表）
    default_fields = ["user_id", "arpu", "traffic_mb", "city", "user_level", "last_active_date"]
    logger.info(f"自动选择字段: {default_fields}")
    return default_fields