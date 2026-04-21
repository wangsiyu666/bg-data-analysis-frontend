"""
向量检索服务：使用 FAISS + Sentence-Transformers 实现。
功能：相似人群扩展、策略库相似检索。
支持本地持久化，无需独立服务进程。
"""
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import faiss
from app.core.config import settings
from app.utils.logger import logger
from typing import List   # 添加这一行

# ========== 配置 ==========
VECTOR_STORAGE_PATH = "/workspace/data/vectors"  # 持久化目录
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # 中文友好，轻量

# ========== 全局变量 ==========
_embedding_model: Optional[SentenceTransformer] = None
_user_store: Optional['FAISSVectorStore'] = None
_strategy_store: Optional['FAISSVectorStore'] = None

class FAISSVectorStore:
    """FAISS 向量存储封装类，支持添加、搜索、保存、加载。"""
    
    def __init__(self, dimension: int, name: str = "default"):
        """
        初始化向量存储。
        
        Args:
            dimension: 向量维度（由嵌入模型决定）
            name: 存储名称（用于日志和文件名）
        """
        self.dimension = dimension
        self.name = name
        self.index = None
        self.metadata = []  # 存储元数据（如 user_id 或策略信息）
        self._init_index()
    
    def _init_index(self):
        """创建 FAISS 索引，使用内积（IP）配合归一化向量实现余弦相似度"""
        self.index = faiss.IndexFlatIP(self.dimension)
        logger.info(f"[FAISS][{self.name}] 索引初始化完成，维度: {self.dimension}")
    
    def add(self, vectors: np.ndarray, metadata_list: List[Any]):
        """
        添加向量和对应的元数据。
        
        Args:
            vectors: shape (n, dimension) 的 numpy 数组，float32
            metadata_list: 长度 n 的列表，每个元素可以是任意类型（如字符串、字典）
        """
        if len(vectors) == 0:
            logger.warning(f"[FAISS][{self.name}] 添加空向量，跳过")
            return
        
        # 归一化向量（内积索引需要）
        faiss.normalize_L2(vectors)
        
        # 添加到索引
        self.index.add(vectors)
        self.metadata.extend(metadata_list)
        
        logger.info(f"[FAISS][{self.name}] 添加 {len(vectors)} 条，总数: {self.index.ntotal}")
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Dict]:
        """
        搜索与查询向量最相似的 k 个结果。
        
        Args:
            query_vector: 查询向量，shape (dimension,)
            k: 返回结果数量
        
        Returns:
            [{"metadata": xxx, "score": similarity_score}, ...]
        """
        if self.index.ntotal == 0:
            logger.warning(f"[FAISS][{self.name}] 索引为空，无法搜索")
            return []
        
        # 确保查询向量是 2D 且归一化
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        faiss.normalize_L2(query_vector)
        
        # 搜索
        scores, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                results.append({
                    "metadata": self.metadata[idx],
                    "score": float(scores[0][i])   # 内积值，归一化后范围 [-1, 1]，越大越相似
                })
        
        logger.info(f"[FAISS][{self.name}] 搜索完成，返回 {len(results)} 条结果")
        return results
    
    def save(self, path: str):
        """将索引和元数据保存到磁盘"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # 保存 FAISS 索引
        faiss.write_index(self.index, f"{path}.index")
        
        # 保存元数据（使用 pickle）
        with open(f"{path}.meta", "wb") as f:
            pickle.dump(self.metadata, f)
        
        logger.info(f"[FAISS][{self.name}] 已保存到 {path}")
    
    def load(self, path: str) -> bool:
        """从磁盘加载索引和元数据，成功返回 True"""
        if not os.path.exists(f"{path}.index"):
            logger.warning(f"[FAISS][{self.name}] 索引文件不存在: {path}.index")
            return False
        
        self.index = faiss.read_index(f"{path}.index")
        with open(f"{path}.meta", "rb") as f:
            self.metadata = pickle.load(f)
        
        logger.info(f"[FAISS][{self.name}] 已加载，包含 {self.index.ntotal} 条向量")
        return True

def init_embedding_model():
    """初始化句子嵌入模型（全局单例）"""
    global _embedding_model
    logger.info(f"[VectorStore] 加载嵌入模型: {EMBEDDING_MODEL_NAME}")
    try:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        dim = _embedding_model.get_sentence_embedding_dimension()
        logger.info(f"[VectorStore] 嵌入模型加载成功，向量维度: {dim}")
    except Exception as e:
        logger.error(f"[VectorStore] 嵌入模型加载失败: {e}", exc_info=True)
        raise

def get_embedding(text: str) -> np.ndarray:
    """获取单个文本的向量表示（已归一化）"""
    global _embedding_model
    if _embedding_model is None:
        init_embedding_model()
    return _embedding_model.encode(text, normalize_embeddings=True)

def get_embeddings_batch(texts: List[str]) -> np.ndarray:
    """批量获取文本向量"""
    global _embedding_model
    if _embedding_model is None:
        init_embedding_model()
    return _embedding_model.encode(texts, normalize_embeddings=True)

def init_vector_stores():
    """初始化所有向量存储（用户库和策略库），并尝试从磁盘加载"""
    global _user_store, _strategy_store
    
    logger.info("[VectorStore] 初始化 FAISS 向量存储...")
    init_embedding_model()
    dim = _embedding_model.get_sentence_embedding_dimension()
    
    # 用户向量存储
    _user_store = FAISSVectorStore(dim, "user")
    user_path = os.path.join(VECTOR_STORAGE_PATH, "user")
    _user_store.load(user_path)
    
    # 策略向量存储
    _strategy_store = FAISSVectorStore(dim, "strategy")
    strategy_path = os.path.join(VECTOR_STORAGE_PATH, "strategy")
    _strategy_store.load(strategy_path)
    
    logger.info("[VectorStore] 初始化完成")

def get_user_store():
    if _user_store is None:
        init_vector_stores()
    return _user_store

def get_strategy_store():
    if _strategy_store is None:
        init_vector_stores()
    return _strategy_store

def add_user_vector(user_id: str, user_features_text: str):
    """添加用户向量（用于相似人群扩展）"""
    store = get_user_store()
    vector = get_embedding(user_features_text)
    store.add(vector.reshape(1, -1), [user_id])
    # 可定期调用 save 持久化，这里简单起见每次添加后保存
    user_path = os.path.join(VECTOR_STORAGE_PATH, "user")
    store.save(user_path)

def find_similar_users(seed_user_id: str, seed_features: str, k: int = 100) -> List[str]:
    """根据种子用户特征查找相似用户"""
    store = get_user_store()
    query_vec = get_embedding(seed_features)
    results = store.search(query_vec, k=k)
    # 排除种子用户自身
    similar = [r["metadata"] for r in results if r["metadata"] != seed_user_id]
    logger.info(f"[VectorStore] 找到 {len(similar)} 个相似用户")
    return similar

def add_strategy_vector(strategy_id: str, strategy_text: str, extra_info: Dict = None):
    """添加策略向量"""
    store = get_strategy_store()
    vector = get_embedding(strategy_text)
    metadata = {"id": strategy_id, "text": strategy_text, "info": extra_info or {}}
    store.add(vector.reshape(1, -1), [metadata])
    strategy_path = os.path.join(VECTOR_STORAGE_PATH, "strategy")
    store.save(strategy_path)

def find_similar_strategies(strategy_text: str, k: int = 5) -> List[Dict]:
    """查找相似历史策略"""
    store = get_strategy_store()
    query_vec = get_embedding(strategy_text)
    results = store.search(query_vec, k=k)
    return results

def save_all_vectors():
    """手动保存所有向量存储"""
    if _user_store:
        _user_store.save(os.path.join(VECTOR_STORAGE_PATH, "user"))
    if _strategy_store:
        _strategy_store.save(os.path.join(VECTOR_STORAGE_PATH, "strategy"))
    logger.info("[VectorStore] 所有向量已持久化")