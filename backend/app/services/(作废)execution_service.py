# ============================================================================
# 文件作用：运营执行优化服务，提供渠道推荐、波次规划、时刻预测
# 能力：基于历史执行计划、客群特征，利用大模型生成个性化执行方案
# 后续使用场景：执行优化智能体调用，为营销活动推荐最佳执行参数
# ============================================================================
import json
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models import ExecutionPlan
from app.services.llm_service import call_llm_sync
from app.utils.logger import logger
from typing import List   # 添加这一行

def get_historical_execution_stats(db: Session, strategy_id: int = None) -> List[Dict]:
    """
    从数据库获取历史执行计划数据（用于参考）
    参数:
        db: 数据库会话
        strategy_id: 可选，限定策略ID
    返回:
        历史执行计划列表，包含渠道、波次、时刻、转化率等
    """
    query = db.query(ExecutionPlan)
    if strategy_id:
        query = query.filter(ExecutionPlan.strategy_id == strategy_id)
    plans = query.order_by(ExecutionPlan.usage_count.desc()).limit(10).all()
    stats = []
    for p in plans:
        stats.append({
            "channel": p.channel,
            "wave_count": p.wave_count,
            "wave_interval_hours": p.wave_interval_hours,
            "send_time_preference": p.send_time_preference,
            "conversion_rate": p.actual_conversion_rate,
            "roi": p.actual_roi,
            "audience_segment": p.audience_segment
        })
    logger.info(f"获取到 {len(stats)} 条历史执行计划数据")
    return stats

def recommend_execution_plan(
    strategy: dict,
    audience_sample: list,
    product_name: str = None,
    db: Session = None
) -> dict:
    """
    执行优化核心：利用大模型推荐渠道、波次、时刻。
    参数:
        strategy: 策略字典（包含 name, description, id）
        audience_sample: 客群样例（前几条数据）
        product_name: 关联产品名称
        db: 数据库会话（用于获取历史数据）
    返回:
        推荐的执行计划字典，包含 channel, wave_count, wave_interval_hours, send_time_preference, reason
    """
    logger.info(f"[执行优化] 开始生成执行计划，策略: {strategy.get('name')}")
    # 获取历史执行计划作为参考
    historical_stats = get_historical_execution_stats(db, strategy.get('id')) if db else []
    historical_text = "\n".join([
        f"- 渠道: {s['channel']}, 波次: {s['wave_count']}, 间隔: {s['wave_interval_hours']}小时, 时刻: {s['send_time_preference']}, 转化率: {s['conversion_rate']}"
        for s in historical_stats[:5]
    ]) if historical_stats else "无历史数据"

    prompt = f"""
你是一个通信运营执行优化专家。请根据以下信息推荐最佳执行方案。
需要输出：渠道（APP推送/短信/人工外呼/电子外呼/营业厅/公众号/小程序/掌上营业厅）、波次数量（1-5）、波次间隔（小时）、发送时刻偏好（如：上午/下午/晚间/个性化）。

策略名称：{strategy.get('name')}
策略描述：{strategy.get('description')}
关联产品：{product_name or '通用'}
客群样例：{audience_sample[:2]}

历史成功执行案例参考：
{historical_text}

请输出 JSON 格式：
{{
  "channel": "推荐渠道",
  "wave_count": 整数,
  "wave_interval_hours": 整数或null,
  "send_time_preference": "时刻偏好",
  "reason": "简要推荐理由"
}}
只输出 JSON。
"""
    response = call_llm_sync(prompt)
    try:
        plan = json.loads(response)
        logger.info(f"执行计划推荐结果: {plan}")
        return plan
    except Exception as e:
        logger.error(f"解析执行计划失败: {e}, 原始响应: {response}")
        # 返回默认计划
        return {
            "channel": "APP推送",
            "wave_count": 3,
            "wave_interval_hours": 24,
            "send_time_preference": "晚间",
            "reason": "默认推荐（解析失败）"
        }

def save_execution_plan(db: Session, plan_data: dict, strategy_id: int, audience_segment: str):
    """
    保存执行计划到数据库（用于后续学习）
    参数:
        db: 数据库会话
        plan_data: 推荐的计划字典
        strategy_id: 关联策略ID
        audience_segment: 客群分群描述
    """
    new_plan = ExecutionPlan(
        strategy_id=strategy_id,
        audience_segment=audience_segment,
        channel=plan_data.get("channel"),
        wave_count=plan_data.get("wave_count", 1),
        wave_interval_hours=plan_data.get("wave_interval_hours"),
        send_time_preference=plan_data.get("send_time_preference"),
        actual_conversion_rate=0.0,
        actual_roi=0.0,
        usage_count=0
    )
    db.add(new_plan)
    db.commit()
    logger.info(f"保存执行计划 ID={new_plan.id}")
    return new_plan