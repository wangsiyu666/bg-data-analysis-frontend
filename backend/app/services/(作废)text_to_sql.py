"""
Text-to-SQL 服务：使用 LangChain 的 SQLDatabaseChain 将自然语言转换为 SQL 并执行。
无需编译，纯 Python 实现。
"""
import re
from typing import Dict, Any, Optional
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from sqlalchemy import create_engine
from app.core.config import settings
from app.utils.logger import logger
from typing import List   # 添加这一行

# 全局变量（单例模式）
_db_chain: Optional[SQLDatabaseChain] = None
_llm: Optional[Ollama] = None
_db: Optional[SQLDatabase] = None

def init_text_to_sql():
    """初始化 Text-to-SQL 链，在应用启动时调用一次"""
    global _db_chain, _llm, _db
    logger.info("[Text-to-SQL] 正在初始化...")

    try:
        # 1. 初始化 Ollama 大模型（温度设为 0 以提高 SQL 准确性）
        _llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.LLM_MODEL,
            temperature=0,
            num_predict=512,
        )
        logger.info(f"[Text-to-SQL] Ollama 模型加载成功: {settings.LLM_MODEL}")

        # 2. 连接 ClickHouse（通过 ClickHouse SQLAlchemy）
        # 注意：ClickHouse 默认用户是 default，无密码
        clickhouse_uri = f"clickhouse://default:@{settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}/default"
        engine = create_engine(clickhouse_uri)
        _db = SQLDatabase(engine, sample_rows_in_table_info=2)  # 每个表取 2 行样例
        logger.info("[Text-to-SQL] ClickHouse 连接成功")

        # 3. 创建 SQLDatabaseChain
        _db_chain = SQLDatabaseChain.from_llm(
            llm=_llm,
            db=_db,
            verbose=True,               # 打印中间步骤，便于调试
            use_query_checker=True,     # 防止生成危险 SQL
            return_intermediate_steps=True,
        )
        logger.info("[Text-to-SQL] SQLDatabaseChain 初始化完成")

    except Exception as e:
        logger.error(f"[Text-to-SQL] 初始化失败: {e}", exc_info=True)
        raise

def generate_sql(question: str) -> Dict[str, Any]:
    """
    将自然语言问题转换为 SQL 并执行，返回结果。
    
    Args:
        question: 用户问题，如 "上个月流量超套用户有多少"
    
    Returns:
        {
            "sql": "生成的 SQL",
            "result": "查询结果文本",
            "intermediate_steps": [...],
            "error": None or str
        }
    """
    global _db_chain
    if _db_chain is None:
        init_text_to_sql()
    
    logger.info(f"[Text-to-SQL] 收到问题: {question}")
    
    try:
        # 调用 SQLDatabaseChain
        response = _db_chain.invoke(question)
        
        # 解析返回结果
        intermediate = response.get("intermediate_steps", [])
        generated_sql = intermediate[0] if intermediate else ""
        
        result = {
            "sql": generated_sql,
            "result": response.get("result", ""),
            "intermediate_steps": intermediate,
            "error": None
        }
        
        logger.info(f"[Text-to-SQL] 生成 SQL: {generated_sql[:200]}...")
        logger.info(f"[Text-to-SQL] 查询结果长度: {len(result['result'])} 字符")
        return result
        
    except Exception as e:
        logger.error(f"[Text-to-SQL] 执行失败: {e}", exc_info=True)
        return {
            "sql": "",
            "result": "",
            "intermediate_steps": [],
            "error": str(e)
        }

def generate_sql_only(question: str) -> str:
    """
    仅生成 SQL 语句，不执行（用于预览）。
    
    Args:
        question: 用户问题
    
    Returns:
        SQL 语句字符串
    """
    global _llm
    if _llm is None:
        init_text_to_sql()
    
    logger.info(f"[Text-to-SQL] 仅生成 SQL（不执行）: {question}")
    
    # 构造专门生成 SQL 的 prompt
    sql_prompt = f"""你是一个 ClickHouse SQL 专家。请根据以下问题生成 ClickHouse SQL 查询语句。
只输出 SQL，不要输出任何解释。不要使用 Markdown 代码块标记。

问题：{question}

SQL："""
    
    try:
        sql = _llm.invoke(sql_prompt)
        # 清理可能残留的 markdown 标记
        sql = re.sub(r'^```sql\n?', '', sql.strip())
        sql = re.sub(r'\n?```$', '', sql)
        logger.info(f"[Text-to-SQL] 生成的 SQL: {sql}")
        return sql
    except Exception as e:
        logger.error(f"[Text-to-SQL] SQL 生成失败: {e}", exc_info=True)
        return ""