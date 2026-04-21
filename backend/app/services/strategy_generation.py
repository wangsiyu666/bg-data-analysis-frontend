# ============================================================================
# 文件功能：策略生成智能体，根据产品、客群（可选）、用户输入生成营销策略
# 符合 PRD 要求：
#   1. 策略名称、策略类别基于用户输入+产品+历史策略生成
#   2. 策略详细描述包含：活动说明、活动政策、扣费方式、有效期、权益内容等（可单独获取）
#   3. 适用条件：独立调用 LLM 基于客群特征生成自然语言描述（若无客群则为空）
#   4. 利用产品信息检索历史相似策略（TOP3）作为参考
# 谁调用：simple_agents, 路由
# ============================================================================
import json
import uuid
from typing import List, Optional
from app.services.clickhouse_service import execute_sql
from app.services.llm_service import call_llm_sync
from app.utils.vector_store import search_similar, add_item
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.strategy import Strategy
from app.utils.logger import logger

# ==================== 客群特征聚合配置（同 product_recommend） ====================
FEATURE_AGGREGATIONS = [
    # 基础属性与消费
    {"field": "age", "agg": "AVG", "desc": "平均年龄", "type": "数值"},
    {"field": "arpu", "agg": "AVG", "desc": "平均ARPU(元)", "type": "数值"},
    {"field": "avg_3mon_fee", "agg": "AVG", "desc": "近3月平均ARPU", "type": "数值"},
    {"field": "amount_bd", "agg": "AVG", "desc": "账户余额波动率", "type": "数值"},
    {"field": "arpu_bd", "agg": "AVG", "desc": "近三月ARPU波动率", "type": "数值"},
    {"field": "pay_fee_3month", "agg": "AVG", "desc": "近三个月缴费金额", "type": "数值"},
    {"field": "owe_fee", "agg": "AVG", "desc": "平均欠费金额", "type": "数值"},
    {"field": "prepay_bal", "agg": "AVG", "desc": "平均账户余额", "type": "数值"},
    # 流量使用
    {"field": "dou", "agg": "AVG", "desc": "平均流量(MB)", "type": "数值"},
    {"field": "all_bhd", "agg": "AVG", "desc": "平均流量饱和度", "type": "数值"},
    {"field": "over_flow_3month", "agg": "AVG", "desc": "近三月套外流量(MB)", "type": "数值"},
    {"field": "is_gprs_ct_3month", "agg": "AVG", "desc": "流量超套比例", "type": "比率"},
    {"field": "gprs_5g_flow_m", "agg": "AVG", "desc": "平均5G流量(GB)", "type": "数值"},
    {"field": "llb_cnt", "agg": "AVG", "desc": "平均流量包个数", "type": "数值"},
    # 语音行为
    {"field": "out_call_duration_m", "agg": "AVG", "desc": "平均主叫时长(分钟)", "type": "数值"},
    {"field": "call_counts", "agg": "AVG", "desc": "平均通话次数", "type": "数值"},
    {"field": "avg_call_duration_m_prv_3m", "agg": "AVG", "desc": "近3月平均通话时长", "type": "数值"},
    {"field": "is_ct_3month", "agg": "AVG", "desc": "语音超套比例", "type": "比率"},
    {"field": "call_opp_counts1", "agg": "AVG", "desc": "平均交往圈人数", "type": "数值"},
    # 套餐与合约
    {"field": "plan_fee", "agg": "AVG", "desc": "平均主套餐价格", "type": "数值"},
    {"field": "is_5gtb", "agg": "AVG", "desc": "5G套包办理比例", "type": "比率"},
    {"field": "plan_5g_mark", "agg": "AVG", "desc": "5G套餐用户比例", "type": "比率"},
    {"field": "plan_six_num", "agg": "AVG", "desc": "近6月换套餐次数", "type": "数值"},
    {"field": "is_jd_3month", "agg": "AVG", "desc": "套餐降档比例", "type": "比率"},
    {"field": "is_heyue", "agg": "AVG", "desc": "合约用户比例", "type": "比率"},
    {"field": "hy_sy_times", "agg": "AVG", "desc": "平均合约剩余时长(月)", "type": "数值"},
    # 活跃与风险
    {"field": "active_mark", "agg": "AVG", "desc": "通信活跃比例", "type": "比率"},
    {"field": "zero_call_days", "agg": "AVG", "desc": "平均0通话天数", "type": "数值"},
    {"field": "ys_yd_yh", "agg": "AVG", "desc": "异动用户比例", "type": "比率"},
    {"field": "ts_counts_3month", "agg": "AVG", "desc": "平均投诉次数", "type": "数值"},
    {"field": "is_ts_high", "agg": "AVG", "desc": "高频投诉比例", "type": "比率"},
    {"field": "quasi_churn", "agg": "AVG", "desc": "准离网比例", "type": "比率"},
    # 异网与社交
    {"field": "yw_call_opp_counts", "agg": "AVG", "desc": "平均异网交往圈人数", "type": "数值"},
    {"field": "yw_in_call_duration", "agg": "AVG", "desc": "平均异网主叫时长", "type": "数值"},
    {"field": "yw_in_call_high", "agg": "AVG", "desc": "异网高话感染比例", "type": "比率"},
    # 生命周期与宽带
    {"field": "user_online", "agg": "AVG", "desc": "平均在网时长(月)", "type": "数值"},
    {"field": "month_new_mark", "agg": "AVG", "desc": "新用户比例", "type": "比率"},
    {"field": "kd_user_mark", "agg": "AVG", "desc": "宽带用户比例", "type": "比率"},
    {"field": "mtd_active_day", "agg": "AVG", "desc": "平均宽带活跃天数", "type": "数值"},
    {"field": "is_fuse", "agg": "AVG", "desc": "捆绑活动用户比例", "type": "比率"},
    # 携转倾向
    {"field": "apply_port_3month", "agg": "AVG", "desc": "携出申请比例", "type": "比率"},
    {"field": "query_port_sms_6month", "agg": "AVG", "desc": "携转查询比例", "type": "比率"},
    {"field": "call_10086_port", "agg": "AVG", "desc": "咨询携转比例", "type": "比率"},
]

def _aggregate_audience_features(audience_ids: List[str]) -> dict:
    """对客群进行多维度特征聚合，返回特征名到数值的字典"""
    if not audience_ids:
        return {}
    sample_ids = audience_ids[:10000]
    ids_str = "','".join([uid.replace("'", "''") for uid in sample_ids])
    select_parts = []
    for feat in FEATURE_AGGREGATIONS:
        if feat["agg"] == "AVG":
            select_parts.append(f"AVG({feat['field']}) as {feat['field']}")
        elif feat["agg"] == "SUM":
            select_parts.append(f"SUM({feat['field']}) as {feat['field']}")
        elif feat["agg"] == "COUNT":
            select_parts.append(f"COUNT({feat['field']}) as {feat['field']}")
    select_clause = ", ".join(select_parts)
    sql = f"SELECT {select_clause} FROM user_behavior WHERE user_id IN ('{ids_str}')"
    result = execute_sql(sql)
    if not result['data']:
        return {}
    row = result['data'][0]
    features = {}
    for idx, feat in enumerate(FEATURE_AGGREGATIONS):
        value = row[idx]
        if value is not None:
            features[feat["desc"]] = float(value)
        else:
            features[feat["desc"]] = 0.0
    return features

def _build_feature_text(features: dict) -> str:
    """将特征字典转换为自然语言描述文本（用于prompt）"""
    parts = []
    for desc, value in features.items():
        if "比例" in desc or "率" in desc:
            parts.append(f"{desc} {value*100:.1f}%")
        elif "金额" in desc or "ARPU" in desc or "余额" in desc or "费用" in desc:
            parts.append(f"{desc} {value:.2f}元")
        elif "时长" in desc or "天数" in desc or "月" in desc:
            parts.append(f"{desc} {value:.1f}")
        else:
            parts.append(f"{desc} {value:.2f}")
    return "，".join(parts)

# ==================== 主函数 ====================
def generate_strategy(user_input: str, product_ids: List[str], audience_ids: Optional[List[str]] = None) -> dict:
    """
    生成策略（符合PRD要求）
    参数:
        user_input: 用户输入的会话信息（运营目标、产品描述等）
        product_ids: 选中的产品ID列表
        audience_ids: 圈选的客群ID列表（可选）
    返回:
        strategy_id 和详细策略信息（包含所有子字段，便于前端分别展示）
    """
    logger.info(f"策略生成，产品: {product_ids}, 客群规模: {len(audience_ids) if audience_ids else 0}")
    db = SessionLocal()
    # 获取产品详情
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    if not products:
        db.close()
        logger.error(f"产品不存在: {product_ids}")
        raise ValueError("产品不存在")
    product_info = "\n".join([f"- {p.name}: {p.description}" for p in products])

    # 客群特征描述（仅用于生成适用条件）
    audience_desc = ""
    audience_scale = 0
    if audience_ids:
        audience_scale = len(audience_ids)
        features = _aggregate_audience_features(audience_ids)
        if features:
            audience_desc = _build_feature_text(features)
        else:
            audience_desc = "无详细特征数据"
    else:
        audience_desc = ""

    # 获取历史相似策略（基于产品名称+用户输入，从 strategies 表中检索 TOP3）
    query_text = f"{user_input} {' '.join([p.name for p in products])}"
    similar_strategies = search_similar("strategies", query_text, top_k=3)
    if not similar_strategies:
        # 降级：直接查询数据库，按产品ID匹配
        product_ids_str = [p.id for p in products]
        db_strategies = db.query(Strategy).filter(Strategy.product_ids.in_(product_ids_str)).limit(3).all()
        similar_strategies = [{
            "metadata": {
                "name": s.name,
                "category": s.category,
                "avg_conversion_rate": s.avg_conversion_rate,
                "avg_roi": s.avg_roi,
                "description": s.description
            }
        } for s in db_strategies]
    similar_text = "\n".join([
        f"- {s['metadata'].get('name', '')} (转化率 {s['metadata'].get('avg_conversion_rate', 0)}，ROI {s['metadata'].get('avg_roi', 0)})"
        for s in similar_strategies
    ]) if similar_strategies else "无历史相似策略"

    # 构建 prompt（要求输出除适用条件外的所有字段，适用条件单独生成）
    # 第一部分：生成策略名称、类别、详细描述等
    prompt_main = f"""
你是一个通信运营专家。请根据以下信息生成一个营销策略。
产品信息：
{product_info}
运营目标/用户输入：
{user_input}
历史相似策略参考：
{similar_text}

请输出 JSON 格式，必须包含以下字段（每个字段都不能缺失，若无内容则输出空字符串）：
{{
    "name": "策略名称",
    "category": "策略类别（挽留/升级/激活/交叉销售）",
    "activity_desc": "活动说明（策略描述）",
    "activity_policy": "活动政策（如优惠力度、参与条件等）",
    "charge_method": "扣费方式（如一次性扣费、按月扣费、免费）",
    "valid_period": "有效期（如30天、当月有效）",
    "rights_content": "权益内容（如赠送天翼云盘2个月会员、赠送定向流量包30G流量等）"
}}
注意：不要生成"conditions"字段，只输出以上7个字段。只输出 JSON。
"""
    response_main = call_llm_sync(prompt_main)
    try:
        if "```json" in response_main:
            response_main = response_main.split("```json")[1].split("```")[0]
        elif "```" in response_main:
            response_main = response_main.split("```")[1].split("```")[0]
        strategy_dict = json.loads(response_main)
        # 确保所有字段都存在
        required_fields = ["name", "category", "activity_desc", "activity_policy", "charge_method", "valid_period", "rights_content"]
        for field in required_fields:
            if field not in strategy_dict:
                strategy_dict[field] = ""
    except Exception as e:
        logger.error(f"LLM 响应解析失败: {e}, 原始响应: {response_main[:200]}")
        strategy_dict = {
            "name": f"{products[0].name}推广策略",
            "category": "升级",
            "activity_desc": f"推广{products[0].name}，提供优惠",
            "activity_policy": "充值100元送20元",
            "charge_method": "按月扣费",
            "valid_period": "30天",
            "rights_content": "赠送10GB流量"
        }

    # 第二部分：生成适用条件（基于客群特征，单独调用 LLM，避免干扰）
    conditions = ""
    if audience_desc:
        prompt_conditions = f"""
你是一个通信运营专家。请根据以下客群特征数据，为营销策略生成一段“适用条件”描述（自然语言，3-5句话）。
客群特征：
{audience_desc}
要求：
- 语言流畅，突出用户画像及口径（如客群年轻化：平均年龄30岁，客群高端化：平均收入45,客群高粘性：40%是融合特征，客群高传播性：平均交往圈人数3人，主要覆盖人群为58-126元之间的4G/5G用户，连续三个月流量使用率超过85%等等）。
- 不要编造数据，只基于提供的特征。
- 不要输出其他内容，只输出适用条件文本。
"""
        try:
            conditions = call_llm_sync(prompt_conditions).strip()
            logger.info(f"LLM 生成适用条件: {conditions[:100]}...")
        except Exception as e:
            logger.error(f"适用条件 LLM 调用失败: {e}")
            conditions = ""
    else:
        conditions = ""

    # 保存策略到数据库
    new_strategy = Strategy(
        id=f"STR_{uuid.uuid4().hex[:8]}",
        name=strategy_dict["name"],
        category=strategy_dict.get("category"),
        description=strategy_dict.get("activity_desc"),
        product_ids=",".join(product_ids),
        conditions=conditions,
        is_active="TRUE"
    )
    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)

    # 向量化新策略
    strategy_text = f"{new_strategy.name} {new_strategy.description} {new_strategy.conditions}"
    add_item("strategies", new_strategy.id, strategy_text, {
        "name": new_strategy.name,
        "category": new_strategy.category,
        "avg_conversion_rate": 0.0,
        "avg_roi": 0.0
    })
    db.close()
    logger.info(f"策略生成并保存，ID: {new_strategy.id}")

    # 构建返回的详情（每个字段独立，便于前端单独获取）
    detail = {
        "name": strategy_dict["name"],
        "category": strategy_dict.get("category"),
        "description": strategy_dict.get("activity_desc"),
        "activity_desc": strategy_dict.get("activity_desc"),
        "activity_policy": strategy_dict.get("activity_policy"),
        "charge_method": strategy_dict.get("charge_method"),
        "valid_period": strategy_dict.get("valid_period"),
        "rights_content": strategy_dict.get("rights_content"),
        "conditions": conditions,
        "audience_scale": audience_scale if audience_ids else None
    }
    return {
        "strategy_id": new_strategy.id,
        "detail": detail
    }