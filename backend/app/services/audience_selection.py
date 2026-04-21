# ============================================================================
# 客群圈选智能体：支持种子扩散、特征组合、产品适配、导入清单四种方式
# 谁调用：simple_agents, 路由
# ============================================================================
import base64
import io
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from app.services.clickhouse_service import execute_sql
from app.services.vanna_service import generate_sql
from app.utils.logger import logger
from app.core.database import SessionLocal
from app.models.product import Product
from app.utils.vector_store import search_similar
from app.services.llm_service import call_llm_sync

# ==================== 全局向量模型（单例） ====================
_model = None

def _get_model():
    """获取 SentenceTransformer 模型（单例）"""
    global _model
    if _model is None:
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        logger.info("向量模型加载完成")
    return _model

# ==================== ====================1.种子扩散法========================================
# 每个字段包含：字段名、描述（用于构建特征文本）
# 从 user_behavior 表中精选约45个代表性字段，覆盖消费、流量、语音、活跃、风险、社交、生命周期、宽带、合约等维度
FEATURE_FIELDS = [
    # 基础属性与消费
    {"field": "age", "desc": "年龄"},
    {"field": "arpu", "desc": "ARPU(元)"},
    {"field": "avg_3mon_fee", "desc": "近3月平均ARPU"},
    {"field": "amount_bd", "desc": "账户余额波动率"},
    {"field": "arpu_bd", "desc": "近三月ARPU波动率"},
    {"field": "pay_fee_3month", "desc": "近三个月缴费金额"},
    {"field": "owe_fee", "desc": "月末欠费金额"},
    {"field": "pve_amount", "desc": "本月账户余额"},
    # 流量使用
    {"field": "dou", "desc": "当月流量(MB)"},
    {"field": "all_bhd", "desc": "当月流量饱和度"},
    {"field": "over_flow_3month", "desc": "近三个月套外流量(MB)"},
    {"field": "is_gprs_ct_3month", "desc": "是否连续3月流量超套"},
    {"field": "gprs_5g_flow_m", "desc": "当月5G流量(GB)"},
    {"field": "gprs_ct", "desc": "当月超套流量"},
    {"field": "llb_cnt", "desc": "生效流量包个数"},
    {"field": "llb_should_fee", "desc": "流量订购费用"},
    # 语音行为
    {"field": "out_call_duration_m", "desc": "本月主叫计费时长(分钟)"},
    {"field": "call_counts", "desc": "当月通话次数"},
    {"field": "avg_call_duration_m_prv_3m", "desc": "连续3月平均通话时长"},
    {"field": "is_ct_3month", "desc": "是否连续3月语音超套"},
    # 套餐与合约
    {"field": "plan_fee", "desc": "主套餐价格"},
    {"field": "plan_six_num", "desc": "近6月换套餐次数"},
    {"field": "is_jd_3month", "desc": "近3月是否套餐降档"},
    {"field": "is_heyue", "desc": "是否合约用户"},
    {"field": "hy_sy_times", "desc": "合约剩余时长(月)"},
    {"field": "is_dx", "desc": "是否参与承诺低消"},
    {"field": "join_new_offer_3month", "desc": "近三月是否参与新增促销"},
    # 活跃与风险
    {"field": "active_mark", "desc": "是否通信用户"},
    {"field": "zero_call_days", "desc": "当月0通话天数"},
    {"field": "ys_yd_yh", "desc": "是否疑似异动用户"},
    {"field": "ts_counts_3month", "desc": "近三个月投诉次数"},
    {"field": "is_ts_high", "desc": "是否高频投诉用户"},
    {"field": "quasi_churn", "desc": "是否准离网"},
    # 异网与社交
    {"field": "yw_call_opp_counts", "desc": "异网交往圈人数"},
    {"field": "yw_in_call_duration", "desc": "与异网主叫通话时长"},
    {"field": "yw_in_call_high", "desc": "是否异网高话感染"},
    # 生命周期与宽带
    {"field": "user_online", "desc": "在网时长(月)"},
    {"field": "month_new_mark", "desc": "是否当月新增用户"},
    {"field": "kd_user_mark", "desc": "是否家庭宽带客户"},
    {"field": "mtd_active_day", "desc": "当月宽带活跃天数"},
    {"field": "is_fuse", "desc": "是否捆绑活动用户"},
    # 携转倾向
    {"field": "apply_port_3month", "desc": "近三月申请过携出"},
    {"field": "query_port_sms_6month", "desc": "近6个月查询携转资格"},
    {"field": "call_10086_port", "desc": "拨打10086咨询携转"},
]


# ==================== 特征向量化函数 ====================
def _get_user_feature_vector(user_id: str):
    """
    从 ClickHouse 获取用户的多维度特征，并转换为向量（所有特征均为数值）
    返回: 向量 (numpy array)，若用户不存在则返回 None
    """
    select_fields = [f["field"] for f in FEATURE_FIELDS]
    if not select_fields:
        logger.error("未配置任何特征字段")
        return None

    field_list = ", ".join(select_fields)
    sql = f"""
    SELECT {field_list}
    FROM user_behavior
    WHERE user_id = '{user_id}'
    LIMIT 1
    """
    result = execute_sql(sql)
    if not result['data']:
        logger.warning(f"未找到用户 {user_id} 的行为数据")
        return None

    row = result['data'][0]
    feature_parts = []
    for idx, field_config in enumerate(FEATURE_FIELDS):
        value = row[idx]
        if value is None or value == '':
            continue
        try:
            num_value = float(value)
            if abs(num_value) > 1e9:
                feature_parts.append(f"{field_config['desc']} 极高")
            else:
                if num_value == int(num_value):
                    feature_parts.append(f"{field_config['desc']} {int(num_value)}")
                else:
                    feature_parts.append(f"{field_config['desc']} {round(num_value, 2)}")
        except (ValueError, TypeError):
            feature_parts.append(f"{field_config['desc']} {value}")

    if not feature_parts:
        logger.warning(f"用户 {user_id} 没有有效特征")
        return None

    feature_text = "，".join(feature_parts)
    logger.debug(f"用户 {user_id} 特征文本长度: {len(feature_text)}")
    model = _get_model()
    vector = model.encode(feature_text)
    return vector

# ==================== 批量解析 user_id/phone_num ====================
def _batch_resolve_user_ids(identifiers: List[str]) -> List[str]:
    """
    批量将输入（user_id 或手机号）转换为 user_id
    使用 UNION ALL 一次性查询，高效转换混合标识，并通过 GROUP BY 去重
    参数: identifiers: 混合标识列表（user_id 或 phone_num）
    返回: 去重后的 user_id 列表（仅存在于数据库中的）
    """
    if not identifiers:
        return []
    escaped = [i.replace("'", "''") for i in identifiers]
    ids_str = "','".join(escaped)
    sql = f"""
        SELECT user_id FROM (
            SELECT user_id FROM user_behavior WHERE user_id IN ('{ids_str}')
            UNION ALL
            SELECT user_id FROM user_behavior WHERE phone_num IN ('{ids_str}')
        ) AS t
        GROUP BY user_id
    """
    result = execute_sql(sql)
    user_ids = [row[0] for row in result['data']]
    logger.info(f"批量转换标识：输入 {len(identifiers)} 个，有效 user_id {len(user_ids)} 个（已去重）")
    return user_ids

# ==================== 余弦相似度 ====================
def _cosine_similarity(vec_a, vec_b):
    """计算两个向量的余弦相似度"""
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

# ==================== 种子扩散法 ====================
def seed_expansion(seed_inputs: List[str], target_count: int) -> List[str]:
    """
    种子扩散法：支持混合输入（user_id 或手机号），基于用户行为向量相似度圈选相似用户
    参数:
        seed_inputs: 种子标识列表（可以是 user_id 或 phone_num）
        target_count: 目标用户量
    返回:
        用户ID列表
    """
    logger.info(f"种子扩散法开始，种子输入数 {len(seed_inputs)}，目标数量 {target_count}")
    if not seed_inputs:
        return []

    # 1. 批量转换为 user_id
    seed_user_ids = _batch_resolve_user_ids(seed_inputs)
    if not seed_user_ids:
        logger.warning("没有有效的种子用户ID，返回空列表")
        return []
    logger.info(f"有效种子用户ID数: {len(seed_user_ids)}")

    # 2. 获取种子用户向量，计算平均向量
    seed_vectors = []
    for uid in seed_user_ids:
        vec = _get_user_feature_vector(uid)
        if vec is not None:
            seed_vectors.append(vec)
    if not seed_vectors:
        logger.warning("没有有效的种子用户向量，返回空列表")
        return []
    avg_vector = np.mean(seed_vectors, axis=0)

    # 3. 获取全体用户（排除种子用户）的 user_id 列表
    sql = "SELECT user_id FROM user_behavior"
    result = execute_sql(sql)
    if not result['data']:
        logger.warning("未获取到任何用户数据，返回空列表")
        return []

    # 4. 计算每个用户与种子平均向量的相似度
    similarities = []
    for row in result['data']:
        uid = row[0]
        if uid in seed_user_ids:
            continue
        vec = _get_user_feature_vector(uid)
        if vec is None:
            continue
        sim = _cosine_similarity(avg_vector, vec)
        similarities.append((uid, sim))

    # 5. 按相似度降序排序，取前 target_count 个
    similarities.sort(key=lambda x: x[1], reverse=True)
    expanded_users = [uid for uid, sim in similarities[:target_count]]
    logger.info(f"种子扩散完成，实际圈选 {len(expanded_users)} 人")
    return expanded_users

# ==================== 特征组合法（修改版：只返回ID和总数，支持预览） ====================
def feature_selection(condition: str = None, fields: List[str] = None, need_preview: bool = False, preview_limit: int = 100, audience_name: str = None) -> dict:
    """
    特征组合法：根据自然语言条件生成SQL并执行，或从已保存的客群中获取用户清单。
    参数:
        condition: 自然语言条件（与 audience_name 二选一）
        fields: 需要返回的字段列表（仅用于预览）
        need_preview: 是否需要返回预览数据
        preview_limit: 预览数据条数
        audience_name: 已保存的客群名称（优先使用）
    返回:
        包含 total, audience_ids, 以及可选 preview_data 的字典
    """
    logger.info(f"特征组合圈选，condition={condition}, audience_name={audience_name}, need_preview={need_preview}")

    # 如果提供了 audience_name，则从 audience_groups 表读取已保存的用户清单
    if audience_name:
        from app.services.clickhouse_service import execute_sql
        # 查询该客群名称下的所有 user_id
        sql = f"SELECT user_id FROM audience_groups WHERE name = '{audience_name}'"
        result = execute_sql(sql)
        audience_ids = [str(row[0]) for row in result['data']] if result['data'] else []
        total = len(audience_ids)
        logger.info(f"从已保存客群 '{audience_name}' 获取到 {total} 个用户")

        result_dict = {
            "audience_ids": audience_ids,
            "total": total
        }

        # 如果需要预览，取前 preview_limit 条数据（仅 user_id 列）
        if need_preview:
            preview_ids = audience_ids[:preview_limit]
            result_dict["preview_data"] = {
                "fields": ["user_id"],
                "data": [[uid] for uid in preview_ids]
            }
        return result_dict
"""
#参数 need_preview 和 preview_limit，当 need_preview=True 且提供了 fields 时，会额外查询前 preview_limit 条详细数据，放在 preview_data 字段中返回。
def feature_selection(condition: str, fields: List[str] = None, need_preview: bool = False, preview_limit: int = 100) -> dict:

    #特征组合法：根据自然语言条件生成SQL并执行
    #参数:
    #    condition: 自然语言条件（如 "arpu > 100 AND user_online < 18"）
    #    fields: 需要返回的字段列表（仅用于预览，如果 need_preview=True 且提供了 fields）
    #    need_preview: 是否需要返回预览数据（前端展示部分用户清单）
    #    preview_limit: 预览数据条数，默认100
    #返回:
    #    包含 audience_ids, total, 以及可选 preview_data 的字典
    
    logger.info(f"特征组合圈选，条件: {condition}, 字段: {fields}, need_preview={need_preview}")
    
    # 1. 获取总用户数（先执行 count 查询）
    count_sql = generate_sql(f"返回满足条件 '{condition}' 的用户数量")
    count_result = execute_sql(count_sql)
    total = count_result['data'][0][0] if count_result['data'] else 0
    logger.info(f"满足条件的用户总数: {total}")
    
    # 2. 获取所有 user_id（只查询 user_id 列，避免传输大量数据）
    id_sql = generate_sql(f"返回满足条件 '{condition}' 的用户的 user_id")
    id_result = execute_sql(id_sql)
    audience_ids = [str(row[0]) for row in id_result['data']] if id_result['data'] else []
    logger.info(f"获取到 user_id 数量: {len(audience_ids)}")
    
    result = {
        "audience_ids": audience_ids,
        "total": total
    }
    
    # 3. 如果需要预览数据，则查询前 preview_limit 条详细字段
    if need_preview and fields:
        preview_sql = generate_sql(f"返回满足条件 '{condition}' 的用户的 {', '.join(fields)} LIMIT {preview_limit}")
        preview_result = execute_sql(preview_sql)
        result["preview_data"] = {
            "fields": preview_result['columns'],
            "data": preview_result['data']
        }
        logger.info(f"预览数据返回 {len(preview_result['data'])} 条")
    
    return result
"""
# ==================== 产品适配客群法 ====================
def product_audience(product_id: str, target_count: int) -> List[str]:
    """
    产品适配客群法：根据产品目标用户类型或描述生成圈选条件，从 ClickHouse 圈选用户
    优先使用 condition_map 精确匹配，否则使用 Vanna 生成 SQL 条件
    参数:
        product_id: 产品ID（对应 products 表的 id）
        target_count: 目标用户量
    返回:
        用户ID列表
    """
    logger.info(f"产品适配圈选，产品ID {product_id}，目标数量 {target_count}")

    # 1. 查询产品信息
    db = SessionLocal()
    product = db.query(Product).filter(Product.id == product_id).first()
    db.close()
    if not product:
        logger.error(f"产品不存在: {product_id}")
        return []

    # 2. 获取目标用户描述（优先 target_user_type，若为空则使用 description）
    target_desc = product.target_user_type
    if not target_desc or target_desc.strip() == "":
        target_desc = product.description
        logger.info(f"产品 target_user_type 为空，使用 description 作为目标描述: {target_desc[:100]}")
    if not target_desc:
        logger.warning(f"产品 {product_id} 既无 target_user_type 也无 description，无法圈选")
        return []

    # 3. 丰富 condition_map（覆盖常见通信行业用户类型）
    condition_map = {
        # 流量类
        "高流量用户": "dou > 5000",
        "低流量用户": "dou < 500",
        "中流量用户": "dou BETWEEN 500 AND 5000",
        "流量超套用户": "is_gprs_ct_3month = 1",
        "流量饱和用户": "all_bhd > 0.9",
        "5G用户": "gprs_5g_flow_m > 0",
        "5G潜在用户": "gprs_5g_flow_m = 0 AND plan_5g_mark = 0 AND dou > 2000",
        "定向流量用户": "is_dxb = 1",
        "流量包订购用户": "llb_cnt > 0",
        "流量零次用户": "dou_mark = 0",
        # 价值类
        "高价值用户": "arpu > 150",
        "低价值用户": "arpu < 50",
        "中价值用户": "arpu BETWEEN 50 AND 150",
        "ARPU下降用户": "arpu_pve1_v < -0.1",
        "消费波动用户": "arpu_bd > 0.3",
        "欠费用户": "owe_fee > 0",
        "高缴费用户": "pay_fee_3month > 500",
        # 语音类
        "高语音用户": "out_call_duration_m > 300",
        "低语音用户": "out_call_duration_m < 30",
        "语音超套用户": "is_ct_3month = 1",
        "零通话用户": "zero_call_days = 30",
        # 活跃度
        "活跃用户": "active_mark = 1",
        "沉默用户": "active_mark = 0",
        "单活用户": "is_dh_3month = 1",
        # 风险/流失
        "流失倾向用户": "ys_yd_yh = 1 OR quasi_churn = 1",
        "异动用户": "ys_yd_yh = 1",
        "准离网用户": "quasi_churn = 1",
        "高投诉用户": "ts_counts_3month > 2",
        "高频投诉用户": "is_ts_high = 1",
        "携转倾向用户": "apply_port_3month = 1 OR query_port_sms_6month = 1",
        "异网高话感染": "yw_in_call_high = 1",
        # 生命周期
        "新用户": "month_new_mark = 1",
        "老用户": "user_online > 24",
        "中年用户": "user_online BETWEEN 12 AND 24",
        "合约用户": "is_heyue = 1",
        "合约到期用户": "hy_sy_times < 3 AND hy_sy_times > 0",
        "合约剩余充足用户": "hy_sy_times > 6",
        # 套餐/产品
        "融合套餐用户": "is_rhtc = 1",
        "5G套餐用户": "plan_5g_mark = 1",
        "套餐降档用户": "is_jd_3month = 1",
        "高频换套餐用户": "plan_six_num > 2",
        # 宽带
        "宽带用户": "kd_user_mark = 1",
        "宽带活跃用户": "mtd_active_day > 20",
        "宽带沉默用户": "mtd_active_day = 0",
        "宽带拆机风险": "kd_cj_3month = 1",
        # 异网/社交
        "异网交往圈大": "yw_call_opp_counts > 10",
        "社交广泛用户": "call_opp_counts1 > 20",
        # 其他
        "校园用户": "school_flag = 1",
        "农村用户": "regiontype_id3 = 1",
        "集团用户": "is_jt = 1",
        "亲情网用户": "is_family = 1",
    }

    condition = condition_map.get(target_desc)
    if condition:
        logger.info(f"精确匹配到条件: {condition}")
    else:
        # 精确匹配失败，使用 Vanna 生成 SQL WHERE 条件
        logger.info(f"未精确匹配，使用 Vanna 生成条件: {target_desc}")
        question = f"返回满足用户类型为「{target_desc}」的用户的 user_id，限制最多 {target_count} 条"
        try:
            sql = generate_sql(question)
            logger.debug(f"Vanna 生成的原始 SQL: {sql}")
            # 提取 WHERE 子句（简单方式）
            if "WHERE" in sql.upper():
                where_part = sql.upper().split("WHERE")[1].split("LIMIT")[0].strip()
                condition = where_part
            else:
                condition = "1=1"
            logger.info(f"Vanna 生成的条件: {condition}")
        except Exception as e:
            logger.error(f"Vanna 生成条件失败: {e}，使用默认条件 1=1")
            condition = "1=1"

    # 4. 执行 ClickHouse 查询
    sql = f"""
        SELECT user_id
        FROM user_behavior
        WHERE {condition}
        LIMIT {target_count}
    """
    logger.debug(f"产品适配最终 SQL: {sql}")
    result = execute_sql(sql)
    if not result['data']:
        logger.info(f"未找到满足条件 '{condition}' 的用户")
        return []

    user_ids = [str(row[0]) for row in result['data']]
    logger.info(f"产品适配圈选完成，实际圈选 {len(user_ids)} 人")
    return user_ids

# ==================== 导入用户清单法 ====================
def import_audience(file_content: str) -> List[str]:
    """
    导入用户清单法：解析 base64 编码的 CSV 文件，并与 user_behavior 表匹配，
    返回存在于数据库中的 user_id 列表（支持 user_id 或 phone_num 混合输入）
    参数:
        file_content: base64 编码的文件内容（每行一个 user_id 或 phone_num）
    返回:
        匹配成功的 user_id 列表（已去重）
    """
    logger.info("导入用户清单法")
    # 1. 解析文件内容
    decoded = base64.b64decode(file_content).decode('utf-8')
    raw_ids = [line.strip() for line in io.StringIO(decoded) if line.strip()]
    logger.info(f"导入原始标识数量: {len(raw_ids)}")

    if not raw_ids:
        return []

    # 2. 批量转换为 user_id（自动去重，只保留数据库中存在的）
    matched_user_ids = _batch_resolve_user_ids(raw_ids)
    logger.info(f"匹配后有效 user_id 数量: {len(matched_user_ids)}")
    return matched_user_ids