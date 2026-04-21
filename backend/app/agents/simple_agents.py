# ============================================================================
# 文件功能：简单智能体封装，供 API 直接调用
# 谁调用：graph（路由）、routes（直接调用）
# 它调用谁：各个 services 中的智能体函数
# ============================================================================
from typing import List
from app.services.audience_analysis import nl2sql, execute_analysis, save_audience, multidim_analysis
from app.services.audience_selection import seed_expansion, feature_selection, product_audience, import_audience
from app.services.product_recommend import recommend_by_text, recommend_by_audience
from app.services.strategy_generation import generate_strategy
from app.services.execution_optimization import optimize_execution
from app.services.evaluation import evaluate_strategy
from app.utils.logger import logger

# ==================== 客群分析 ====================
def run_nl2sql(question: str, user_id: str):
    logger.info(f"简单调用: NL2SQL, 用户 {user_id}")
    return nl2sql(question)

def run_execute_sql(sql: str, user_id: str):
    logger.info(f"简单调用: 执行SQL, 用户 {user_id}")
    return execute_analysis(sql)

def run_save_audience(name: str, condition_sql: str, user_id: str):
    logger.info(f"简单调用: 保存客群, 用户 {user_id}")
    return save_audience(name, condition_sql)

def run_multidim_analysis(base_sql: str, user_id: str):
    logger.info(f"简单调用: 多维分析, 用户 {user_id}")
    return multidim_analysis(base_sql)

# ==================== 客群圈选 ====================
def run_seed_expansion(seed_users: List[str], target_count: int, user_id: str):
    logger.info(f"简单调用: 种子扩散, 用户 {user_id}")
    return seed_expansion(seed_users, target_count)


def run_feature_selection(condition: str = None, fields: List[str] = None, need_preview: bool = False, preview_limit: int = 100, audience_name: str = None, user_id: str = "system"):
    logger.info(f"简单调用: 特征组合, 用户 {user_id}, need_preview={need_preview}, audience_name={audience_name}")
    return feature_selection(condition, fields, need_preview, preview_limit, audience_name)

def run_product_audience(product_id: str, target_count: int, user_id: str):
    logger.info(f"简单调用: 产品适配圈选, 用户 {user_id}")
    return product_audience(product_id, target_count)

def run_import_audience(file_content: str, user_id: str):
    logger.info(f"简单调用: 导入清单, 用户 {user_id}")
    return import_audience(file_content)

# ==================== 产品推荐 ====================
def run_recommend_by_text(user_input: str, user_id: str):
    logger.info(f"简单调用: 文本推荐产品, 用户 {user_id}")
    return recommend_by_text(user_input)

def run_recommend_by_audience(audience_ids: List[str], user_input: str, user_id: str):
    logger.info(f"简单调用: 客群推荐产品, 用户 {user_id}")
    return recommend_by_audience(audience_ids, user_input)

# ==================== 策略生成 ====================
def run_generate_strategy(user_input: str, product_ids: List[str], audience_ids: List[str], user_id: str):
    logger.info(f"简单调用: 生成策略, 用户 {user_id}")
    return generate_strategy(user_input, product_ids, audience_ids)

# ==================== 执行优化 ====================
def run_optimize_execution(user_input: str, product_ids: List[str], strategy_id: str, audience_ids: List[str], user_id: str):
    logger.info(f"简单调用: 执行优化, 用户 {user_id}")
    return optimize_execution(user_input, product_ids, strategy_id, audience_ids)

# ==================== 效果评估 ====================
def run_evaluate_strategy(strategy_id: str, user_id: str):
    logger.info(f"简单调用: 效果评估, 用户 {user_id}")
    return evaluate_strategy(strategy_id)
