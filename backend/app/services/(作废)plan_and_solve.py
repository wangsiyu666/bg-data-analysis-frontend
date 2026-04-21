# ============================================================================
# 文件作用：Plan-and-Solve 动态规划引擎，将复杂用户目标分解为多个步骤并执行
# 能力：使用 LLM 生成计划，再通过 LangGraph 动态构建工作流，实现自动化多步任务
# 后续使用场景：当用户输入包含"然后"、"接着"等关键词时自动触发
# ============================================================================
import json
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.services.llm_service import call_llm_sync
from app.agents.simple_agents import *
from app.utils.logger import logger
from typing import List   # 添加这一行

class PlanState(Dict):
    """计划执行状态，继承字典，用于 LangGraph 状态传递"""
    pass

def generate_plan(user_goal: str) -> dict:
    """
    使用 LLM 将用户目标分解为一系列可执行步骤。
    
    参数:
        user_goal: 用户自然语言描述的目标
    
    返回:
        包含 steps 的字典，每个 step 有 agent, params, output_key, depends_on 等
    """
    prompt = f"""
你是一个运营任务规划专家。请将以下用户目标分解为可执行的步骤。
可用智能体（agent）：
- zero_code_analytics: 输入自然语言问题，返回数据结果。参数 {{"question": "问题"}}
- audience_selection: 输入客群条件，返回客群数据（含字段）。参数 {{"condition": "条件"}}
- strategy_generation: 输入客群数据和目标，返回策略方案。参数 {{"audience_data": "客群数据", "goal": "目标"}}
- execution_optimization: 输入策略和客群，返回执行计划。参数 {{"strategy": "策略", "audience_ids": []}}
- evaluation: 输入活动ID，返回效果评估。参数 {{"campaign_id": "ID"}}
- script_generation: 输入策略和客群样例，返回话术。参数 {{"strategy": "策略", "audience_sample": "客群样例", "product_name": "产品名称"}}

用户目标：{user_goal}

请输出 JSON 格式的计划，格式如下：
{{
  "steps": [
    {{"agent": "audience_selection", "params": {{"condition": "..."}}, "output_key": "audience", "depends_on": []}},
    {{"agent": "strategy_generation", "params": {{"audience_key": "audience", "goal": "..."}}, "output_key": "strategy", "depends_on": ["audience"]}}
  ]
}}
只输出 JSON，不要有其他文字。
"""
    response = call_llm_sync(prompt)
    try:
        # 去除可能的 markdown 代码块标记
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        plan = json.loads(response)
        logger.info(f"生成计划成功，共 {len(plan['steps'])} 步")
        return plan
    except Exception as e:
        logger.error(f"计划解析失败: {e}, 原始响应: {response[:200]}")
        return {"steps": []}

def execute_plan(plan: dict, initial_state: dict, db_session) -> dict:
    """
    动态执行计划，根据依赖关系构建 LangGraph 工作流并运行。
    
    参数:
        plan: 计划字典
        initial_state: 初始状态（包含 user_input, user_id 等）
        db_session: 数据库会话
    
    返回:
        最终状态字典
    """
    from app.agents.simple_agents import (
        run_zero_code_analytics, run_audience_selection, run_strategy_generation,
        run_execution_optimization, run_evaluation, run_script_generation
    )
    
    agent_map = {
        "zero_code_analytics": run_zero_code_analytics,
        "audience_selection": run_audience_selection,
        "strategy_generation": run_strategy_generation,
        "execution_optimization": run_execution_optimization,
        "evaluation": run_evaluation,
        "script_generation": run_script_generation
    }
    
    workflow = StateGraph(PlanState)
    steps = plan.get("steps", [])
    if not steps:
        logger.warning("计划为空，直接返回初始状态")
        return initial_state
    
    # 为每个步骤添加节点
    for step in steps:
        agent_name = step["agent"]
        node_func = agent_map.get(agent_name)
        if not node_func:
            logger.error(f"未知的智能体: {agent_name}")
            continue
        
        # 闭包函数，用于封装节点逻辑
        def make_node(func, params, output_key):
            def node(state):
                # 解析参数：如果参数值以 "_key" 结尾，则从 state 中获取对应的值
                resolved_params = {}
                for k, v in params.items():
                    if isinstance(v, str) and v.endswith("_key") and v[:-4] in state:
                        resolved_params[k] = state[v[:-4]]
                    else:
                        resolved_params[k] = v
                # 根据智能体类型调用不同函数
                if agent_name == "audience_selection":
                    result = func(condition=resolved_params.get("condition"), user_id=state.get("user_id", "system"))
                elif agent_name == "strategy_generation":
                    result = func(audience_data=resolved_params.get("audience_data"), goal=resolved_params.get("goal"), db_session=db_session)
                elif agent_name == "execution_optimization":
                    result = func(
                        strategy=resolved_params.get("strategy"),
                        audience_data=resolved_params.get("audience_data"),
                        db_session=db_session
                    )
                elif agent_name == "script_generation":
                    result = func(
                        strategy=resolved_params.get("strategy"),
                        audience_sample=resolved_params.get("audience_sample"),
                        product_name=resolved_params.get("product_name"),
                        user_id=state.get("user_id", "system")
                    )
                else:
                    result = func(**resolved_params)
                state[output_key] = result
                return state
            return node
        
        workflow.add_node(step["output_key"], make_node(node_func, step.get("params", {}), step["output_key"]))
    
    # 添加边（依赖关系）
    entry_nodes = []
    for step in steps:
        output_key = step["output_key"]
        deps = step.get("depends_on", [])
        if not deps:
            entry_nodes.append(output_key)
        else:
            for dep in deps:
                workflow.add_edge(dep, output_key)
    
    if entry_nodes:
        workflow.set_entry_point(entry_nodes[0])
        for node in entry_nodes[1:]:
            workflow.add_edge(entry_nodes[0], node)
    
    last_node = steps[-1]["output_key"]
    workflow.add_edge(last_node, END)
    
    # 编译并执行
    app = workflow.compile()
    final_state = app.invoke(initial_state)
    logger.info("计划执行完成")
    return final_state