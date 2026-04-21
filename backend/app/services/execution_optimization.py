# ============================================================================
# 文件功能：策略执行智能体（策略执行优化）
# 根据运营者输入、产品信息、策略信息以及历史相似策略，生成：
#   - 2个推荐渠道（主推 + 次推）
#   - 每个渠道配备2套营销话术（共4套话术）
#   - 营销频率（波次数量）和波次间隔
#   - 最佳营销时刻（星期 + 具体时刻）
# 并将生成的话术和执行计划持久化到数据库。
# 
# 调用关系：
#   - 被调用：simple_agents.run_optimize_execution()  -> 本文件中的 optimize_execution()
#   - 调用者：
#       * app.services.llm_service.call_llm_sync       (调用大模型生成内容)
#       * app.utils.vector_store.search_similar        (检索历史相似策略)
#       * app.core.database.SessionLocal               (获取数据库会话)
#       * app.models.strategy.Strategy                 (策略表模型)
#       * app.models.product.Product                   (产品表模型)
#       * app.models.script.Script                     (话术表模型)
#       * app.models.execution_plan.ExecutionPlan      (执行计划表模型)
#       * app.utils.logger.logger                      (日志)
# ============================================================================
import json
import uuid
from typing import List, Dict, Any
from app.services.llm_service import call_llm_sync
from app.utils.vector_store import search_similar
from app.core.database import SessionLocal
from app.models.strategy import Strategy
from app.models.product import Product
from app.models.script import Script
from app.models.execution_plan import ExecutionPlan
from app.utils.logger import logger

# ==================== 辅助函数：获取历史相似策略信息 ====================
"""
    根据产品ID和策略描述，通过向量检索获取 TOP3 历史相似策略，
    并从中提取出历史常用的渠道、话术、波次、时刻偏好等信息。
    
    参数:
        product_ids: 产品ID列表
        user_input: 运营者输入的自然语言描述
        strategy: 当前生成的策略对象
    
    返回:
        字典，包含四个列表：
        {
            "channels": [历史推荐渠道列表],
            "scripts": [历史话术片段列表],
            "waves": [历史波次数量列表],
            "time_preferences": [历史时刻偏好描述列表]
        }
"""
def _get_historical_strategy_info(product_ids: List[str], user_input: str, strategy: Strategy) -> Dict[str, Any]:
    logger.info("检索历史相似策略（TOP3）...")
    query_text = f"{user_input} {strategy.name} {strategy.description} {' '.join(product_ids)}"
    similar = search_similar("strategies", query_text, top_k=3)
    if not similar:
        logger.warning("未找到历史相似策略")
        return {"channels": [], "scripts": [], "waves": [], "time_preferences": []}
    
    historical_channels = []
    historical_scripts = []
    historical_waves = []
    historical_time_prefs = []
    db = SessionLocal()
    for item in similar:
        meta = item.get("metadata", {})
        if meta.get("channel_preference"):
            historical_channels.append(meta["channel_preference"])
        if meta.get("wave_count"):
            historical_waves.append(meta["wave_count"])
        if meta.get("send_time_preference"):
            historical_time_prefs.append(meta["send_time_preference"])
        if meta.get("strategy_id"):
            try:
                scripts = db.query(Script).filter(Script.strategy_id == meta["strategy_id"]).limit(2).all()
                for s in scripts:
                    historical_scripts.append(s.content[:50])
            except Exception as e:
                logger.error(f"查询历史话术失败: {e}")
    db.close()
    return {"channels": historical_channels, "scripts": historical_scripts, "waves": historical_waves, "time_preferences": historical_time_prefs}


# ==================== 主函数：执行优化 ====================
def optimize_execution(user_input: str, product_ids: List[str], strategy_id: str, audience_ids: List[str] = None) -> dict:
    """
    执行优化：生成渠道推荐、话术、营销频率、最佳营销时刻，并持久化到数据库。
    
    参数:
        user_input: 运营者输入的自然语言（运营目标、产品描述等）
        product_ids: 选中的产品ID列表
        strategy_id: 生成的策略ID
        audience_ids: 圈选的客群ID列表（当前未直接使用，但保留用于未来扩展）
    
    返回:
        字典，包含：
        {
            "channels": [{"channel": "渠道名", "scripts": ["话术1","话术2"]}, ...],  # 2个渠道，每个2套话术
            "wave_count": int,                 # 波次数量
            "wave_interval_hours": int,        # 波次间隔（小时）
            "time_preference": {               # 最佳营销时刻
                "weekdays": ["一","三","五"],
                "times": ["10:00","15:00"]
            },
            "plan_id": str,                    # 执行计划ID
            "script_ids": List[str]            # 生成的话术ID列表
        }
    """
    logger.info(f"执行优化开始: 策略ID={strategy_id}, 产品IDs={product_ids}, 客群规模={len(audience_ids) if audience_ids else 0}")
    
    db = SessionLocal()
    
    # 1. 获取策略和产品详细信息
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        db.close()
        raise ValueError(f"策略不存在: {strategy_id}")
    
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    if not products:
        db.close()
        raise ValueError(f"产品不存在: {product_ids}")
    
    product_info = "\n".join([f"- {p.name}: {p.description}" for p in products])
    logger.debug(f"策略信息: {strategy.name}, 产品信息: {product_info[:200]}")
    
    # 2. 获取历史相似策略的参考信息（TOP3）
    historical = _get_historical_strategy_info(product_ids, user_input, strategy)
    hist_channels = "、".join(historical["channels"]) if historical["channels"] else "无"
    hist_scripts = "\n".join([f"- {s}" for s in historical["scripts"][:3]]) if historical["scripts"] else "无"
    hist_waves = "、".join(historical["waves"]) if historical["waves"] else "无"
    hist_time = "、".join(historical["time_preferences"]) if historical["time_preferences"] else "无"
    
    # 3. 构建提示词（明确要求输出2个渠道，每个渠道2套话术）
    prompt = f"""
你是通信运营专家。请根据以下信息，生成一个完整的执行方案。

【产品信息】
{product_info}

【策略信息】
名称：{strategy.name}
描述：{strategy.description}
适用条件：{strategy.conditions}

【用户输入/运营目标】
{user_input}

【历史相似策略参考】
- 常用渠道：{hist_channels}
- 常用话术示例：{hist_scripts}
- 常用波次：{hist_waves}
- 常用时刻偏好：{hist_time}

【输出要求】
请输出 JSON 格式，必须严格遵循以下结构：
{{
    "channels": [
        {{"channel": "主推渠道名称", "scripts": ["话术1", "话术2"]}},
        {{"channel": "次推渠道名称", "scripts": ["话术3", "话术4"]}}
    ],
    "wave_count": 整数（1-5，代表波次数量）,
    "wave_interval_hours": 整数（小时，波次间隔）,
    "time_preference": {{
        "weekdays": ["一", "二", "三", "四", "五", "六", "日"],  // 可多选，如 ["一","三","五"]
        "times": ["HH:MM", "HH:MM"]  // 可多个时刻，如 ["10:00", "15:00"]
    }}
}}
注意：
- 必须输出 2 个渠道，每个渠道必须包含 2 套话术（共 4 套话术）。
- 渠道名称例如：短信、APP推送、外呼、邮件、微信公众号等。
- 话术要贴合产品、策略和客群特征，语气亲切，包含行动号召。
- 波次数量建议 1-3，波次间隔通常 24 或 48 小时。
- 时刻偏好建议选择用户活跃的时段（如工作日晚上、周末下午等）。
只输出 JSON，不要有任何其他文字。
"""
    # 调用大模型
    response = call_llm_sync(prompt, timeout=90)
    logger.debug(f"LLM 原始响应: {response[:200]}...")
    
    # 4. 解析 LLM 返回的 JSON，并进行格式校验与修正
    try:
        # 清理可能包含的 markdown 代码块标记
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        data = json.loads(response)
        
        # 校验渠道数量是否为2
        if len(data.get("channels", [])) != 2:
            logger.warning(f"LLM 返回的渠道数量不是2个: {len(data.get('channels', []))}，强制修正为默认值")
            data["channels"] = [
                {"channel": "短信", "scripts": ["尊敬的用户，流量包限时优惠...", "亲爱的用户，专属福利..."]},
                {"channel": "APP推送", "scripts": ["打开APP领取流量...", "会员日特惠..."]}
            ]
        # 校验每个渠道的话术数量是否为2
        for idx, ch in enumerate(data["channels"]):
            if len(ch.get("scripts", [])) != 2:
                logger.warning(f"渠道 {ch['channel']} 的话术数量不是2套: {len(ch.get('scripts', []))}，强制修正")
                data["channels"][idx]["scripts"] = ["默认话术1", "默认话术2"]
    except Exception as e:
        logger.error(f"解析 LLM 响应失败: {e}, 原始响应: {response[:200]}")
        # 使用安全的默认值
        data = {
            "channels": [
                {"channel": "短信", "scripts": ["尊敬的用户，流量包限时优惠...", "亲爱的用户，专属福利..."]},
                {"channel": "APP推送", "scripts": ["打开APP领取流量...", "会员日特惠..."]}
            ],
            "wave_count": 2,
            "wave_interval_hours": 24,
            "time_preference": {"weekdays": ["一", "三"], "times": ["12:00", "18:00"]}
        }
    
    # 5. 保存生成的话术到 scripts 表
    script_ids = []
    for ch in data["channels"]:
        for script_text in ch["scripts"]:
            script = Script(
                id=f"SCR_{uuid.uuid4().hex[:8]}",
                content=script_text,
                channel=ch["channel"],
                strategy_id=strategy_id,
                product_id=",".join(product_ids)
            )
            db.add(script)
            db.flush()          # 获取自增ID（若需要）
            script_ids.append(script.id)
    logger.info(f"已保存 {len(script_ids)} 条话术")
    
    # 6. 保存执行计划到 execution_plans 表
    plan = ExecutionPlan(
        id=f"PLAN_{uuid.uuid4().hex[:8]}",
        strategy_id=strategy_id,
        channel=data["channels"][0]["channel"],          # 主推渠道作为计划主渠道
        wave_count=str(data["wave_count"]),
        wave_interval_hours=str(data["wave_interval_hours"]),
        send_time_preference=str(data["time_preference"])
    )
    db.add(plan)
    db.commit()
    db.close()
    
    # 7. 输出详细日志（便于调试和验证）
    logger.info(f"执行优化完成：生成 {len(data['channels'])} 个渠道")
    for idx, ch in enumerate(data["channels"]):
        logger.info(f"  渠道{idx+1}: {ch['channel']}，话术数量 {len(ch['scripts'])} 套")
        for sidx, script in enumerate(ch["scripts"]):
            logger.debug(f"    话术{sidx+1}: {script[:60]}...")
    logger.info(f"波次: {data['wave_count']}，间隔: {data['wave_interval_hours']}小时，时刻偏好: {data['time_preference']}")
    
    return {
        "channels": data["channels"],
        "wave_count": data["wave_count"],
        "wave_interval_hours": data["wave_interval_hours"],
        "time_preference": data["time_preference"],
        "plan_id": plan.id,
        "script_ids": script_ids
    }