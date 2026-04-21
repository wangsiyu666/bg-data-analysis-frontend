# ============================================================================
# 文件功能：LLMCompiler 动态任务规划引擎，根据场景生成执行计划（产品运营法/客群运营法）
# 谁调用：graph（当需要全流程编排时）
# 它调用谁：
#   - app.services.llm_service.call_llm_sync（调用大模型生成计划）
#   - app.agents.simple_agents（各个智能体的具体执行函数）
#   - app.utils.logger.logger（日志）
# ============================================================================
import json
from typing import List, Dict
from app.services.llm_service import call_llm_sync
from app.agents.simple_agents import *
from app.utils.logger import logger

# ==================== 客群圈选分发函数 ====================
"""
    根据 method 分发到不同的客群圈选函数
    参数:
        method: "seed" | "feature" | "product" | "import"
        kwargs: 其他参数（如 seed_users, condition, product_id, file_content 等）
    返回:
        圈选结果（包含 audience_ids 和 total 的字典）
"""
def _audience_selection_dispatch(method: str, **kwargs):
    logger.info(f"客群圈选分发: method={method}, kwargs={kwargs}")
    if method == "seed":
        return run_seed_expansion(
            kwargs.get("seed_users", []),
            kwargs.get("target_count", 1000),
            kwargs.get("user_id", "system")
        )
    elif method == "feature":
        return run_feature_selection(
            kwargs.get("condition", ""),
            kwargs.get("fields"),
            need_preview=False,
            preview_limit=100,
            user_id=kwargs.get("user_id", "system")
        )
    elif method == "product":
        return run_product_audience(
            kwargs.get("product_id"),
            kwargs.get("target_count", 1000),
            kwargs.get("user_id", "system")
        )
    elif method == "import":
        return run_import_audience(
            kwargs.get("file_content", ""),
            kwargs.get("user_id", "system")
        )
    else:
        raise ValueError(f"未知圈选方法: {method}")

# ==================== LLMCompiler 类 ====================
"""
    动态任务规划引擎
    功能：
        1. 根据场景（产品运营法/客群运营法）生成执行计划（步骤列表）
        2. 按顺序执行计划，自动处理变量替换（如 $products[0].id）
"""

class LLMCompiler:
    # ... __init__ 不变
    def plan(self, scenario: str, context: dict) -> list:
        logger.info(f"LLMCompiler 生成计划: scenario={scenario}, context={context}")
        if scenario == "product_based":
            plan = [
                {"agent": "product_recommend", "params": {"user_input": context["user_input"]}, "output": "products"},
                {"agent": "audience_selection", "params": {"method": "product", "product_id": "$products[0].id", "target_count": 1000, "user_id": context.get("user_id", "system")}, "output": "audience"},
                {"agent": "strategy_generation", "params": {"user_input": context["user_input"], "product_ids": "$products[*].id", "audience_ids": "$audience.audience_ids", "user_id": context.get("user_id", "system")}, "output": "strategy"},
                {"agent": "execution_optimization", "params": {"user_input": context["user_input"], "product_ids": "$products[*].id", "strategy_id": "$strategy.strategy_id", "audience_ids": "$audience.audience_ids", "user_id": context.get("user_id", "system")}, "output": "execution"},
                {"agent": "evaluation", "params": {"strategy_id": "$strategy.strategy_id", "user_id": context.get("user_id", "system")}, "output": "evaluation"}
            ]
        else:
            plan = [
                {"agent": "audience_selection", "params": {"method": "feature", "condition": context.get("condition", ""), "user_id": context.get("user_id", "system")}, "output": "audience"},
                {"agent": "product_recommend", "params": {"method": "audience", "audience_ids": "$audience.audience_ids", "user_input": context["user_input"], "user_id": context.get("user_id", "system")}, "output": "products"},
                {"agent": "strategy_generation", "params": {"user_input": context["user_input"], "product_ids": "$products[*].id", "audience_ids": "$audience.audience_ids", "user_id": context.get("user_id", "system")}, "output": "strategy"},
                {"agent": "execution_optimization", "params": {"user_input": context["user_input"], "product_ids": "$products[*].id", "strategy_id": "$strategy.strategy_id", "audience_ids": "$audience.audience_ids", "user_id": context.get("user_id", "system")}, "output": "execution"},
                {"agent": "evaluation", "params": {"strategy_id": "$strategy.strategy_id", "user_id": context.get("user_id", "system")}, "output": "evaluation"}
            ]
        logger.info(f"生成的计划: {plan}")
        return plan

    def plan(self, scenario: str, context: dict) -> list:
        """
        根据场景生成执行计划
        参数:
            scenario: "product_based" 或 "audience_based"
            context: 包含 user_input, condition 等上下文信息
        返回:
            步骤列表，每个步骤包含 agent, params, output 等字段
        """
        logger.info(f"LLMCompiler 生成计划: scenario={scenario}, context={context}")
        if scenario == "product_based":
            # 产品运营法执行顺序：
            # 1. 产品推荐（基于用户输入）
            # 2. 客群圈选（基于推荐出的产品，使用产品适配法）
            # 3. 策略生成（基于产品+客群）
            # 4. 执行优化（生成渠道、话术等）
            # 5. 效果评估
            plan = [
                {
                    "agent": "product_recommend",
                    "params": {"user_input": context["user_input"]},
                    "output": "products"
                },
                {
                    "agent": "audience_selection",
                    "params": {
                        "method": "product",
                        "product_id": "$products[0].id",
                        "target_count": 1000
                    },
                    "output": "audience"
                },
                {
                    "agent": "strategy_generation",
                    "params": {
                        "user_input": context["user_input"],
                        "product_ids": "$products[*].id",
                        "audience_ids": "$audience.audience_ids"
                    },
                    "output": "strategy"
                },
                {
                    "agent": "execution_optimization",
                    "params": {
                        "user_input": context["user_input"],
                        "product_ids": "$products[*].id",
                        "strategy_id": "$strategy.strategy_id",
                        "audience_ids": "$audience.audience_ids"
                    },
                    "output": "execution"
                },
                {
                    "agent": "evaluation",
                    "params": {"strategy_id": "$strategy.strategy_id"},
                    "output": "evaluation"
                }
            ]
        else:  # audience_based
            # 客群运营法执行顺序：
            # 1. 客群圈选（基于特征组合法，条件来自 context）
            # 2. 产品推荐（基于圈选出的客群）
            # 3. 策略生成（基于产品+客群）
            # 4. 执行优化
            # 5. 效果评估
            plan = [
                {
                    "agent": "audience_selection",
                    "params": {
                        "method": "feature",
                        "condition": context.get("condition", "")
                    },
                    "output": "audience"
                },
                {
                    "agent": "product_recommend",
                    "params": {
                        "method": "audience",
                        "audience_ids": "$audience.audience_ids",
                        "user_input": context["user_input"]
                    },
                    "output": "products"
                },
                {
                    "agent": "strategy_generation",
                    "params": {
                        "user_input": context["user_input"],
                        "product_ids": "$products[*].id",
                        "audience_ids": "$audience.audience_ids"
                    },
                    "output": "strategy"
                },
                {
                    "agent": "execution_optimization",
                    "params": {
                        "user_input": context["user_input"],
                        "product_ids": "$products[*].id",
                        "strategy_id": "$strategy.strategy_id",
                        "audience_ids": "$audience.audience_ids"
                    },
                    "output": "execution"
                },
                {
                    "agent": "evaluation",
                    "params": {"strategy_id": "$strategy.strategy_id"},
                    "output": "evaluation"
                }
            ]
        logger.info(f"生成的计划: {plan}")
        return plan

    def execute(self, plan: list, context: dict) -> dict:
        """
        执行计划，按顺序运行每个步骤，并处理变量替换
        参数:
            plan: 步骤列表（由 plan() 生成）
            context: 初始上下文（通常包含 user_input 等）
        返回:
            执行完所有步骤后的最终上下文（包含每个步骤的输出）
        """
        result_context = context.copy()
        logger.info("开始执行计划，初始上下文: %s", result_context)

        for step_idx, step in enumerate(plan):
            agent_name = step["agent"]
            params = step.get("params", {})
            output_key = step.get("output", f"{agent_name}_result")

            # 变量替换：参数值如果以 "$" 开头，则从 result_context 中取值
            resolved_params = {}
            for k, v in params.items():
                if isinstance(v, str) and v.startswith("$"):
                    # 解析路径，例如 "$products[0].id"
                    # 先去掉开头的 "$"
                    path = v[1:]
                    parts = path.split(".")
                    val = result_context
                    for part in parts:
                        # 处理数组索引，如 "products[0]"
                        if "[" in part and "]" in part:
                            arr_name, idx_str = part.split("[")
                            idx = int(idx_str.rstrip("]"))
                            val = val.get(arr_name, [])[idx]
                        else:
                            val = val.get(part, {})
                    resolved_params[k] = val
                else:
                    resolved_params[k] = v

            logger.info(f"执行步骤 {step_idx+1}: agent={agent_name}, 参数={resolved_params}")

            # 获取对应的函数并调用
            func = self.available_agents.get(agent_name)
            if not func:
                raise ValueError(f"未知智能体: {agent_name}")

            result = func(**resolved_params)
            result_context[output_key] = result
            logger.debug(f"步骤输出: {output_key} = {result}")

        logger.info("计划执行完成")
        return result_context


# 全局单例实例
compiler = LLMCompiler()