# ============================================================================
# 文件作用：话术库服务，提供话术向量检索、保存、合规检查等功能
# 能力：基于历史话术和合规规则，辅助生成高质量营销话术
# 后续使用场景：话术生成智能体中检索相似话术、合规检查
# ============================================================================
from typing import List, Dict
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
from app.models.script import Script
from app.utils.logger import logger
from typing import List   # 添加这一行

# 初始化向量模型（复用策略服务的模型）
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
chroma_client = chromadb.PersistentClient(path="/workspace/data/vectors")
script_collection = chroma_client.get_or_create_collection(
    name="script_vectors",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name='paraphrase-multilingual-MiniLM-L12-v2'
    )
)

# 合规敏感词库（可配置）
SENSITIVE_WORDS = ["最", "唯一", "绝对", "第一", "顶级", "国家级", "全网最低"]

def check_compliance(content: str) -> dict:
    """
    检查话术合规性：返回是否通过及命中词列表
    """
    hit_words = [w for w in SENSITIVE_WORDS if w in content]
    is_compliant = len(hit_words) == 0
    if not is_compliant:
        logger.warning(f"话术包含敏感词: {hit_words}")
    return {"compliant": is_compliant, "hit_words": hit_words}

def sync_scripts_to_vector_db(db: Session):
    """将数据库中的所有话术同步到向量库（用于检索）"""
    scripts = db.query(Script).filter(Script.compliance_status == 'approved').all()
    if not scripts:
        logger.warning("没有找到合规话术，跳过同步")
        return
    ids, embeddings, metadatas = [], [], []
    for sc in scripts:
        text = sc.content
        embedding = model.encode(text).tolist()
        ids.append(str(sc.id))
        embeddings.append(embedding)
        metadatas.append({
            "scenario": sc.scenario,
            "product_id": sc.product_id,
            "strategy_id": sc.strategy_id,
            "user_segment": sc.user_segment,
            "channel": sc.channel,
            "usage_count": sc.usage_count,
            "avg_ctr": sc.avg_ctr
        })
    if ids:
        script_collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)
    logger.info(f"同步 {len(scripts)} 条话术到向量库")

def search_similar_scripts(query_text: str, top_k: int = 3, db: Session = None) -> List[Dict]:
    """向量检索相似话术"""
    logger.info(f"检索相似话术，查询: {query_text[:50]}...")
    results = script_collection.query(query_texts=[query_text], n_results=top_k)
    if not results['ids']:
        return []
    similar = []
    for idx, sid in enumerate(results['ids'][0]):
        metadata = results['metadatas'][0][idx]
        similar.append({
            "id": int(sid),
            "scenario": metadata.get("scenario"),
            "product_id": metadata.get("product_id"),
            "strategy_id": metadata.get("strategy_id"),
            "user_segment": metadata.get("user_segment"),
            "channel": metadata.get("channel"),
            "usage_count": metadata.get("usage_count", 0),
            "avg_ctr": metadata.get("avg_ctr", 0.0)
        })
    logger.info(f"检索到 {len(similar)} 个相似话术")
    return similar

def save_script(db: Session, script_data: dict) -> Script:
    """保存新话术到数据库，并同步向量库"""
    # 合规检查
    compliance = check_compliance(script_data["content"])
    status = "approved" if compliance["compliant"] else "blocked"
    new_script = Script(
        content=script_data["content"],
        scenario=script_data.get("scenario"),
        product_id=script_data.get("product_id"),
        strategy_id=script_data.get("strategy_id"),
        user_segment=script_data.get("user_segment"),
        channel=script_data.get("channel"),
        compliance_status=status,
        usage_count=0,
        avg_ctr=0.0
    )
    db.add(new_script)
    db.commit()
    db.refresh(new_script)

    if status == "approved":
        # 同步到向量库
        embedding = model.encode(new_script.content).tolist()
        script_collection.upsert(
            ids=[str(new_script.id)],
            embeddings=[embedding],
            metadatas=[{
                "scenario": new_script.scenario,
                "product_id": new_script.product_id,
                "strategy_id": new_script.strategy_id,
                "user_segment": new_script.user_segment,
                "channel": new_script.channel,
                "usage_count": 0,
                "avg_ctr": 0.0
            }]
        )
    logger.info(f"保存话术 ID={new_script.id}, 合规状态={status}")
    return new_script