# ============================================================================
# 统一向量存储管理（产品、策略、话术），用于相似性检索
#需要存储和检索向量（产品、策略、话术的语义向量），用于相似度匹配（如产品推荐、相似策略检索）。直接操作 ChromaDB 复杂，需要封装。
# 谁调用：product_recommend, strategy_generation, execution_optimization
# ============================================================================
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from app.utils.logger import logger

_chroma_client = None
_collections = {}

def get_vector_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path="/workspace/data/vectors")
        logger.info("ChromaDB 客户端初始化完成")
    return _chroma_client

def get_collection(name: str):
    if name not in _collections:
        client = get_vector_client()
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='paraphrase-multilingual-MiniLM-L12-v2')
        _collections[name] = client.get_or_create_collection(name=name, embedding_function=embedding_fn)
        logger.info(f"集合 {name} 已就绪")
    return _collections[name]

def add_item(collection_name: str, item_id: str, text: str, metadata: dict):
    coll = get_collection(collection_name)
    coll.upsert(ids=[item_id], documents=[text], metadatas=[metadata])
    logger.debug(f"添加向量: {collection_name}/{item_id}")

def search_similar(collection_name: str, query: str, top_k: int = 5):
    coll = get_collection(collection_name)
    results = coll.query(query_texts=[query], n_results=top_k)
    if results['ids'] and results['ids'][0]:
        items = []
        for i, idx in enumerate(results['ids'][0]):
            items.append({
                "id": idx,
                "score": results['distances'][0][i] if results.get('distances') else 0,
                "metadata": results['metadatas'][0][i] if results.get('metadatas') else {}
            })
        logger.info(f"从 {collection_name} 检索到 {len(items)} 个相似项")
        return items
    return []