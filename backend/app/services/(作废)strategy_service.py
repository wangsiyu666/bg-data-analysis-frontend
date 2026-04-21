
# ============================================================================
# 文件作用：将PostgreSQL中的策略库、产品库、话术库、执行计划表数据同步到向量库，包含向量检索相似策略、保存策略、同步向量库
# 能力：基于 ChromaDB 实现语义搜索，从历史策略中找到相似案例，辅助新策略生成
# 后续使用场景：策略生成智能体中检索相似策略，以及策略管理功能
# ============================================================================
# 替换 sqlite3 为 pysqlite3（解决 ChromaDB sqlite3 版本要求）
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.strategy import Strategy
from app.utils.logger import logger
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

# ========== 初始化向量模型和 ChromaDB ==========
# SentenceTransformer 是一个预训练的句子嵌入模型，将文本转换为向量
# 'paraphrase-multilingual-MiniLM-L12-v2' 是多语言模型，支持中文
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# ChromaDB 持久化客户端，数据保存在 /workspace/data/vectors 目录
chroma_client = chromadb.PersistentClient(path="/workspace/data/vectors")

# 创建或获取 collection（相当于数据库中的表），使用 SentenceTransformer 作为 embedding 函数
collection = chroma_client.get_or_create_collection(
    name="strategy_vectors",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name='paraphrase-multilingual-MiniLM-L12-v2'
    )
)

def sync_strategies_to_vector_db(db: Session):
    """将数据库中的所有策略同步到向量库（用于检索）"""
    strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
    if not strategies:
        logger.warning("没有找到任何策略，跳过同步")
        return
    ids, embeddings, metadatas = [], [], []
    for st in strategies:
        # 将策略名称、描述、条件拼接成文本
        text = f"{st.name} {st.description} {st.conditions}"
        # encode 方法将文本转换为向量（list of float）
        embedding = model.encode(text).tolist()
        ids.append(str(st.id))
        embeddings.append(embedding)
        metadatas.append({
            "name": st.name,
            "category": st.category,
            "avg_conversion_rate": st.avg_conversion_rate,
            "avg_roi": st.avg_roi,
            "avg_click_rate": st.avg_click_rate
        })
    if ids:
        # upsert: 如果 id 存在则更新，否则插入
        collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)
    logger.info(f"同步 {len(strategies)} 条策略到向量库")

def search_similar_strategies(query_text: str, top_k: int = 3, db: Session = None) -> List[Dict]:
    """
    向量检索相似策略。
    
    参数:
        query_text: 查询文本（如策略描述或目标）
        top_k: 返回最相似的个数
        db: 数据库会话（可选，用于补充详细信息）
    
    返回:
        策略信息列表，包含 id, name, category, 历史效果指标等
    """
    logger.info(f"检索相似策略，查询: {query_text[:50]}...")
    # query 方法：查询与 query_text 最相似的 top_k 个向量
    results = collection.query(query_texts=[query_text], n_results=top_k)
    if not results['ids']:
        logger.info("未找到相似策略")
        return []
    
    similar = []
    for idx, sid in enumerate(results['ids'][0]):
        metadata = results['metadatas'][0][idx]
        similar.append({
            "id": int(sid),
            "name": metadata.get("name"),
            "category": metadata.get("category"),
            "avg_conversion_rate": metadata.get("avg_conversion_rate", 0.0),
            "avg_roi": metadata.get("avg_roi", 0.0),
            "avg_click_rate": metadata.get("avg_click_rate", 0.0)
        })
    logger.info(f"检索到 {len(similar)} 个相似策略")
    return similar

def save_strategy(db: Session, strategy_data: dict) -> Strategy:
    """
    保存新策略到数据库，并同步到向量库。
    
    参数:
        db: 数据库会话
        strategy_data: 策略字典，包含 name, category, description, product_ids, conditions, channel_preference, discount_ratio
    """
    new_strategy = Strategy(
        name=strategy_data["name"],
        category=strategy_data.get("category"),
        description=strategy_data["description"],
        product_ids=",".join(map(str, strategy_data.get("product_ids", []))),
        conditions=strategy_data.get("conditions"),
        channel_preference=strategy_data.get("channel_preference"),
        discount_ratio=strategy_data.get("discount_ratio", 0.0)
    )
    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)
    
    # 同步到向量库
    text = f"{new_strategy.name} {new_strategy.description} {new_strategy.conditions}"
    embedding = model.encode(text).tolist()
    collection.upsert(
        ids=[str(new_strategy.id)],
        embeddings=[embedding],
        metadatas=[{
            "name": new_strategy.name,
            "category": new_strategy.category,
            "avg_conversion_rate": 0.0,
            "avg_roi": 0.0
        }]
    )
    logger.info(f"保存策略 ID={new_strategy.id}, 名称={new_strategy.name}")
    return new_strategy

def get_strategy_by_id(db: Session, strategy_id: int) -> Strategy:
    """根据 ID 获取策略"""
    return db.query(Strategy).filter(Strategy.id == strategy_id).first()