# ============================================================================
# 文件功能：产品推荐智能体，提供两种产品推荐方法
# 1. 基于文本推荐（recommend_by_text）：用户输入自然语言描述，LLM 提取候选产品名称，再向量检索匹配产品库
# 2. 基于客群推荐（recommend_by_audience）：根据圈选的客群ID列表，聚合多维度特征，LLM 推荐候选产品名称，再向量检索匹配产品库
# 谁调用：simple_agents（包装后供路由调用），routes.py 中的 /product/recommend_by_text 和 /product/recommend_by_audience 接口
# 它调用谁：
#   - app.core.database.SessionLocal：获取数据库会话
#   - app.models.product.Product：产品表模型
#   - app.services.clickhouse_service.execute_sql：执行 ClickHouse 查询（客群特征聚合）
#   - app.services.llm_service.call_llm_sync：调用大模型生成候选产品名称
#   - app.utils.vector_store.search_similar：向量检索产品库
#   - app.utils.logger.logger：记录日志
# ============================================================================
from typing import List, Dict
from app.core.database import SessionLocal
from app.models.product import Product
from app.services.clickhouse_service import execute_sql
from app.services.llm_service import call_llm_sync
from app.utils.vector_store import search_similar
from app.utils.logger import logger

# ==================== 客群多维度特征聚合配置（用于 recommend_by_audience） ====================
# 定义特征类别及其对应的 SQL 聚合表达式
# 每个特征包含：字段名、聚合方式、描述、数据类型（数值/比率）
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

# ==================== 辅助函数：客群特征聚合 ====================
def _aggregate_audience_features(audience_ids: List[str]) -> Dict[str, float]:
    """
    对客群进行多维度特征聚合，返回特征名到数值的字典
    参数:
        audience_ids: 客群用户ID列表
    返回:
        特征字典，如 {"平均ARPU": 120.5, "流量超套比例": 0.3, ...}
    """
    if not audience_ids:
        return {}
    # 限制采样数量（避免 SQL 过长，同时保证聚合效率）
    sample_ids = audience_ids[:10000]
    ids_str = "','".join([uid.replace("'", "''") for uid in sample_ids])
    # 动态构建 SELECT 子句
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
        logger.warning("客群特征聚合无数据")
        return {}
    row = result['data'][0]
    features = {}
    for idx, feat in enumerate(FEATURE_AGGREGATIONS):
        value = row[idx]
        if value is not None:
            features[feat["desc"]] = float(value)
        else:
            features[feat["desc"]] = 0.0
    logger.info(f"客群特征聚合完成，共 {len(features)} 个特征")
    return features

def _build_feature_text(features: Dict[str, float]) -> str:
    """
    将特征字典转换为自然语言描述文本
    参数:
        features: 特征名到数值的字典
    返回:
        可读的特征文本，如“平均ARPU 120.5元，流量超套比例 30.0%...”
    """
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

# ==================== 公共辅助函数：LLM 生成候选名称 + 向量检索匹配 ====================
def _llm_to_products(candidate_names: List[str], top_k: int) -> List[dict]:
    """
    根据 LLM 生成的产品名称列表，通过向量检索匹配产品库，返回去重后的产品详情
    参数:
        candidate_names: LLM 返回的产品名称列表（可能不精确）
        top_k: 最多返回的产品数量
    返回:
        产品详情列表
    """
    if not candidate_names:
        return []
    db = SessionLocal()
    products = []
    used_product_ids = set()
    for name in candidate_names[:top_k * 2]:  # 多取一些，防止重复
        try:
            similar = search_similar("products", name, top_k=1)
            if similar and similar[0]["id"] not in used_product_ids:
                product_id = similar[0]["id"]
                p = db.query(Product).filter(Product.id == product_id).first()
                if p:
                    products.append({
                        "id": p.id,
                        "name": p.name,
                        "category": p.category,
                        "price": p.price,
                        "description": p.description,
                        "applicable_scope": p.applicable_scope
                    })
                    used_product_ids.add(product_id)
                    logger.info(f"向量检索匹配: LLM名称 '{name}' -> 产品 '{p.name}' (相似度: {similar[0]['score']:.4f})")
                else:
                    logger.warning(f"向量检索返回的产品ID {product_id} 在数据库中不存在")
        except Exception as e:
            logger.error(f"向量检索异常: {e}")
            continue
    db.close()
    # 去重后若不足 top_k，补充默认产品
    if len(products) < top_k:
        logger.info(f"实际匹配到 {len(products)} 个产品，不足 {top_k}，补充默认产品")
        db = SessionLocal()
        existing_ids = [p["id"] for p in products]
        default_products = db.query(Product).filter(Product.id.notin_(existing_ids)).limit(top_k - len(products)).all()
        for p in default_products:
            products.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "description": p.description,
                "applicable_scope": p.applicable_scope
            })
        db.close()
    return products[:top_k]

# ==================== 回退方案：直接向量检索 ====================
def _direct_vector_search(query: str, top_k: int) -> List[dict]:
    """
    直接对查询文本进行向量检索，返回最相似的产品（回退方案）
    参数:
        query: 查询文本
        top_k: 返回数量
    返回:
        产品详情列表
    """
    try:
        similar = search_similar("products", query, top_k=top_k)
        if not similar:
            logger.warning("直接向量检索未返回任何产品")
            return []
    except Exception as e:
        logger.error(f"直接向量检索失败: {e}")
        return []
    db = SessionLocal()
    products = []
    for item in similar:
        p = db.query(Product).filter(Product.id == item["id"]).first()
        if p:
            products.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "description": p.description,
                "applicable_scope": p.applicable_scope
            })
    db.close()
    return products

# ==================== 基于文本推荐 ====================
def recommend_by_text(user_input: str, top_k: int = 4) -> List[dict]:
    """
    基于运营者输入的文本，通过 LLM 提取候选产品名称，再向量检索匹配产品库
    参数:
        user_input: 用户输入的会话信息（如“推广5G流量包给高流量用户”）
        top_k: 返回产品数量，默认4
    返回:
        产品详情列表
    """
    logger.info(f"基于文本推荐产品，输入: {user_input[:100]}...")
    if not user_input or not user_input.strip():
        return []

    # 1. 调用 LLM 生成候选产品名称列表（例如 3-5 个）
    prompt = f"""
你是一个通信产品专家。根据以下用户需求，推荐 {top_k} 个最合适的产品名称（从流量包、5G套餐、融合套餐、语音包、权益包等不限上述这些，但要符合通信行业实际产品中选择）。
用户需求：{user_input}
要求：只输出产品名称列表，每行一个产品名称，不要有任何其他文字。
示例输出：
5G尊享流量包
千兆宽带融合套餐
腾讯视频会员权益包
"""
    try:
        response = call_llm_sync(prompt, timeout=60)
        llm_names = [line.strip() for line in response.split('\n') if line.strip()]
        logger.info(f"LLM 生成候选产品名称: {llm_names}")
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}，回退到直接向量检索")
        return _direct_vector_search(user_input, top_k)

    if not llm_names:
        logger.warning("LLM 未返回任何产品名称，回退到直接向量检索")
        return _direct_vector_search(user_input, top_k)

    # 2. 对每个候选名称进行向量检索匹配
    return _llm_to_products(llm_names, top_k)

# ==================== 基于客群推荐 ====================
def recommend_by_audience(audience_ids: List[str], user_input: str = "", top_k: int = 4) -> List[dict]:
    """
    基于圈选的客群多维度特征，调用 LLM 推荐候选产品名称，再向量检索匹配产品库
    参数:
        audience_ids: 前端圈选并传入的客群用户ID列表
        user_input: 补充需求描述（可选）
        top_k: 返回产品数量，默认4
    返回:
        产品详情列表
    """
    logger.info(f"基于客群推荐，客群规模 {len(audience_ids)}，补充输入: {user_input[:100] if user_input else ''}")
    if not audience_ids:
        logger.warning("客群为空，无法推荐")
        return []

    # 1. 聚合客群多维度特征
    features = _aggregate_audience_features(audience_ids)
    if not features:
        logger.warning("客群特征聚合失败，返回空列表")
        return []
    feature_text = _build_feature_text(features)
    logger.debug(f"客群特征摘要: {feature_text[:300]}...")

    # 2. 调用 LLM 生成产品推荐（返回产品名称列表）
    prompt = f"""
你是一个通信产品专家。根据以下客群的多维度特征，推荐 {top_k} 个最合适的产品名称（从流量包、5G套餐、融合套餐、语音包、权益包等不限上述这些，但要符合通信行业实际产品中选择）。
客群特征：{feature_text}
补充需求：{user_input if user_input else '无'}
要求：只输出产品名称列表，每行一个产品名称，不要有任何其他文字。
示例输出：
5G尊享流量包
千兆宽带融合套餐
腾讯视频会员权益包
"""
    try:
        response = call_llm_sync(prompt, timeout=60)
        llm_names = [line.strip() for line in response.split('\n') if line.strip()]
        logger.info(f"LLM 推荐产品名称: {llm_names}")
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}，返回空列表")
        return []

    if not llm_names:
        logger.warning("LLM 未返回任何产品名称")
        return []

    # 3. 对每个候选名称进行向量检索匹配
    return _llm_to_products(llm_names, top_k)