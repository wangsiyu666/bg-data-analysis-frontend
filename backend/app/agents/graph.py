# ============================================================================
# 混合模式入口（PRD不需要意图判断，直接根据前端请求调用对应智能体或LLMCompiler）
# 谁调用：workflow_tasks（Celery）
# ============================================================================
from app.agents.simple_agents import *
from app.agents.llm_compiler import compiler
from app.utils.logger import logger
from typing import List   # 添加这一行

def route_user_request(action: str, params: dict) -> dict:
    """
    根据前端传递的 action 调用对应的智能体或执行计划
    action 值: nl2sql, execute_sql, save_audience, multidim_analysis,
               seed_expansion, feature_selection, product_audience, import_audience,
               recommend_by_text, recommend_by_audience,
               generate_strategy, optimize_execution, evaluate_strategy,
               product_based_flow, audience_based_flow
    """
    logger.info(f"路由请求: action={action}, params={params}")
    if action == "nl2sql":
        return run_nl2sql(params["question"], params.get("user_id", "system"))
    elif action == "execute_sql":
        return run_execute_sql(params["sql"], params.get("user_id", "system"))
    elif action == "save_audience":
        return run_save_audience(params["name"], params["condition_sql"], params.get("user_id", "system"))
    elif action == "multidim_analysis":
        return run_multidim_analysis(params["base_sql"], params.get("user_id", "system"))
    elif action == "seed_expansion":
        return run_seed_expansion(params["seed_users"], params["target_count"], params.get("user_id", "system"))
    elif action == "feature_selection":
        return run_feature_selection(params["condition"], params.get("fields"), params.get("user_id", "system"))
    elif action == "product_audience":
        return run_product_audience(params["product_id"], params["target_count"], params.get("user_id", "system"))
    elif action == "import_audience":
        return run_import_audience(params["file_content"], params.get("user_id", "system"))
    elif action == "recommend_by_text":
        return run_recommend_by_text(params["user_input"], params.get("user_id", "system"))
    elif action == "recommend_by_audience":
        return run_recommend_by_audience(params["audience_ids"], params.get("user_input", ""), params.get("user_id", "system"))
    elif action == "generate_strategy":
        return run_generate_strategy(params["user_input"], params["product_ids"], params.get("audience_ids"), params.get("user_id", "system"))
    elif action == "optimize_execution":
        return run_optimize_execution(params["user_input"], params["product_ids"], params["strategy_id"], params.get("audience_ids"), params.get("user_id", "system"))
    elif action == "evaluate_strategy":
        return run_evaluate_strategy(params["strategy_id"], params.get("user_id", "system"))
    elif action == "product_based_flow":
        # 全流程产品运营法
        context = {"user_input": params["user_input"]}
        plan = compiler.plan("product_based", context)
        return compiler.execute(plan, context)
    elif action == "audience_based_flow":
        context = {"user_input": params["user_input"], "condition": params.get("condition", "")}
        plan = compiler.plan("audience_based", context)
        return compiler.execute(plan, context)
    else:
        return {"error": f"未知 action: {action}"}