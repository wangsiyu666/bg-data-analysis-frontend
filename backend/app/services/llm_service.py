# ============================================================================
# 大模型调用服务（Ollama），提供同步/异步调用，带超时和重试
# 谁调用：所有需要生成文本的智能体（策略生成、话术生成等）
# ============================================================================
import httpx
from app.core.config import settings
from app.utils.logger import logger
from typing import List   # 添加这一行

async def call_llm_async(prompt: str, timeout: float = 120.0) -> str:
    """
    异步调用 Ollama 模型
    参数:
        prompt: 提示词
        timeout: 超时时间（秒）
    返回:
        模型生成的文本
    """
    logger.info(f"调用 Ollama 模型: {settings.LLM_MODEL}, 提示词长度: {len(prompt)}")
    async with httpx.AsyncClient(timeout=timeout) as client:
        payload = {
            "model": settings.LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7, "top_p": 0.9}
        }
        try:
            response = await client.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload)
            response.raise_for_status()
            result = response.json().get("response", "")
            logger.info(f"LLM 调用成功，返回长度: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}", exc_info=True)
            raise

#提供一个同步接口，用于在无法使用 async/await 的环境（比如 LangGraph 的节点函数）中调用大模型
#
def call_llm_sync(prompt: str, timeout: float = 120.0) -> str:
    """
    同步调用 Ollama（用于 LangGraph 节点中无法使用 async 的场景）
    """
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():    #判断是否存在一个正在运行的事件循环
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(call_llm_async(prompt, timeout))
    else:
        return asyncio.run(call_llm_async(prompt, timeout))