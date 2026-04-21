# ============================================================================
# 效果评估智能体：基于历史相似策略加权平均计算预测指标
# 谁调用：simple_agents, 路由
# 1. 从数据库获取策略信息
# 2. 使用向量检索找到最相似的 5 条历史策略用向量检索 search_similar("strategies", strategy.description, top_k=5) 找到最相似的5个历史策略。
# 3.根据相似度分数计算权重：对每个相似策略，根据相似度分数（距离）计算权重：weight = 1 / (score + 0.001)。
# 4.加权平均得到预测指标：加权平均计算 predicted_conversion_rate, predicted_roi, predicted_click_rate。
#被调用：simple_agents.run_evaluate_strategy() → 此函数
#调用：
#app.utils.vector_store.search_similar（检索相似策略）
#app.core.database.SessionLocal（查询策略详情）
#app.models.strategy.Strategy（策略表模型）
# ============================================================================
from app.utils.vector_store import search_similar
from app.core.database import SessionLocal
from app.models.strategy import Strategy
from app.utils.logger import logger
from typing import List   # 添加这一行

def evaluate_strategy(strategy_id: str) -> dict:
    """
    评估策略效果
    参数: strategy_id: 策略ID
    返回: 预测转化率、ROI、接通率
    """
    logger.info(f"评估策略 {strategy_id}")
    db = SessionLocal()
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    db.close()
    if not strategy:
        raise ValueError("策略不存在")
    similar = search_similar("strategies", strategy.description, top_k=5)
    total_weight = 0.0
    conv = roi = click = 0.0
    for item in similar:
        weight = 1.0 / (item.get("score", 1.0) + 0.001)
        total_weight += weight
        meta = item.get("metadata", {})
        conv += float(meta.get("avg_conversion_rate", 0)) * weight
        roi += float(meta.get("avg_roi", 0)) * weight
        click += float(meta.get("avg_click_rate", 0)) * weight
    if total_weight > 0:
        conv /= total_weight
        roi /= total_weight
        click /= total_weight
    logger.info(f"评估结果: 转化率 {conv:.2f}, ROI {roi:.2f}, 接通率 {click:.2f}")
    return {
        "predicted_conversion_rate": round(conv, 4),
        "predicted_roi": round(roi, 4),
        "predicted_click_rate": round(click, 4)
    }