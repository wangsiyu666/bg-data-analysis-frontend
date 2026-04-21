# ============================================================================
# 文件功能：FastAPI 路由定义，提供所有 API 端点（完全匹配 PRD 交互）
# 谁调用：main.py（注册路由）
# 它调用谁：
#   - app.tasks.workflow_tasks.process_user_request（异步任务）
#   - app.agents.simple_agents（各智能体直接调用）
#   - app.utils.sensitive_filter（敏感信息脱敏）
#   - app.services.clickhouse_service.execute_sql（获取字段）
#   - celery.result.AsyncResult（轮询任务结果）
# ============================================================================
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.tasks.workflow_tasks import process_user_request
from app.agents.simple_agents import *
from app.models.schemas import *
from celery.result import AsyncResult
from app.tasks.celery_app import celery_app
from app.utils.sensitive_filter import filter_sensitive_data, mask_user_id, mask_phone
from app.services.clickhouse_service import execute_sql
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["telecompass"])

# ==================== 统一入口（混合模式） ====================
@router.post("/unified")
# async def unified_endpoint(request: NLQueryRequest):
async def unified_endpoint(request: NL2SQLRequest):
    """
    统一入口：混合模式自动路由（简单指令直接调用，复杂指令走 Plan-and-Solve）
    返回 task_id，前端轮询获取结果。
    """
    logger.info(f"统一入口请求: {request.user_id} -> {request.question}")
    task = process_user_request.delay(request.question, request.user_id)
    return {"task_id": task.id, "status": "processing"}

@router.get("/result/{task_id}")
async def get_task_result(task_id: str):
    """轮询异步任务结果"""
    result = AsyncResult(task_id, app=celery_app)
    if result.ready():
        if result.successful():
            data = result.result
            filtered = filter_sensitive_data(data)
            return {"status": "completed", "data": filtered}
        else:
            return {"status": "failed", "data": {"error": str(result.info)}}
    return {"status": "pending"}

# ==================== 客群分析 ====================
@router.post("/audience/nl2sql", response_model=NL2SQLResponse)
async def audience_nl2sql(request: NL2SQLRequest):
    logger.info(f"NL2SQL 请求: {request.question}")
    return run_nl2sql(request.question, request.user_id)

@router.post("/audience/execute", response_model=ExecuteSQLResponse)
async def audience_execute(request: ExecuteSQLRequest):
    logger.info(f"执行SQL请求: {request.sql[:100]}")
    result = run_execute_sql(request.sql, request.user_id)
    return filter_sensitive_data(result)

@router.post("/audience/save", response_model=MessageResponse)
async def audience_save(request: SaveAudienceRequest):
    logger.info(f"保存客群: {request.name}")
    run_save_audience(request.name, request.condition_sql, request.user_id)
    return MessageResponse(message="保存成功")
#多为分析作废，改为前端
@router.post("/audience/multidim", response_model=MultidimAnalysisResponse)
async def audience_multidim(request: MultidimAnalysisRequest):
    logger.info(f"多维分析请求，基础SQL: {request.base_sql}")
    return run_multidim_analysis(request.base_sql, request.user_id)

# ==================== 客群圈选 ====================
@router.post("/audience/seed", response_model=AudienceSelectionResponse)
async def audience_seed(request: SeedExpansionRequest):
    logger.info(f"种子扩散: 种子用户数 {len(request.seed_users)}, 目标 {request.target_count}")
    ids = run_seed_expansion(request.seed_users, request.target_count, request.user_id)
    return AudienceSelectionResponse(audience_ids=ids, total=len(ids))

@router.post("/audience/feature", response_model=AudienceSelectionResponse)
async def audience_feature(request: FeatureSelectionRequest):
    logger.info(f"特征组合: condition={request.condition}, audience_name={request.audience_name}")
    result = run_feature_selection(
        condition=request.condition,
        fields=request.fields,
        need_preview=False,
        audience_name=request.audience_name,
        user_id=request.user_id
    )
    return AudienceSelectionResponse(audience_ids=result["audience_ids"], total=result["total"])

@router.post("/audience/feature/preview")
async def audience_feature_preview(request: FeatureSelectionRequest, limit: int = 100):
    MAX_PREVIEW_LIMIT = 500
    if limit > MAX_PREVIEW_LIMIT:
        limit = MAX_PREVIEW_LIMIT
        logger.warning(f"预览请求 limit 超过 {MAX_PREVIEW_LIMIT}，已限制为 {MAX_PREVIEW_LIMIT}")

    logger.info(f"特征组合预览: condition={request.condition}, audience_name={request.audience_name}, limit={limit}")
    result = run_feature_selection(
        condition=request.condition,
        fields=request.fields,
        need_preview=True,
        preview_limit=limit,
        audience_name=request.audience_name,
        user_id=request.user_id
    )
    preview = result.get("preview_data", {})
    fields = preview.get("fields", [])
    data = preview.get("data", [])

    # 对敏感字段脱敏（如果存在 user_id）
    if data and fields:
        uid_idx = -1
        phone_idx = -1
        for i, f in enumerate(fields):
            if f.lower() == "user_id":
                uid_idx = i
            elif f.lower() == "phone_num":
                phone_idx = i
        if uid_idx != -1 or phone_idx != -1:
            for row in data:
                if uid_idx != -1 and len(row) > uid_idx:
                    row[uid_idx] = mask_user_id(str(row[uid_idx]))
                if phone_idx != -1 and len(row) > phone_idx:
                    row[phone_idx] = mask_phone(str(row[phone_idx]))

    return {"fields": fields, "data": data}

@router.post("/audience/product", response_model=AudienceSelectionResponse)
async def audience_product(request: ProductAudienceRequest):
    logger.info(f"产品适配圈选: 产品 {request.product_id}, 目标 {request.target_count}")
    ids = run_product_audience(request.product_id, request.target_count, request.user_id)
    return AudienceSelectionResponse(audience_ids=ids, total=len(ids))

@router.post("/audience/import", response_model=AudienceSelectionResponse)
async def audience_import(request: ImportAudienceRequest):
    logger.info("导入用户清单")
    ids = run_import_audience(request.file_content, request.user_id)
    return AudienceSelectionResponse(audience_ids=ids, total=len(ids))

# ==================== 产品推荐 ====================
@router.post("/product/recommend_by_text", response_model=ProductRecommendResponse)
async def product_recommend_text(request: ProductRecommendByTextRequest):
    logger.info(f"文本推荐产品: {request.user_input}")
    products = run_recommend_by_text(request.user_input, request.user_id)
    return ProductRecommendResponse(products=products)

@router.post("/product/recommend_by_audience", response_model=ProductRecommendResponse)
async def product_recommend_audience(request: ProductRecommendByAudienceRequest):
    logger.info(f"客群推荐产品，客群规模 {len(request.audience_ids)}")
    products = run_recommend_by_audience(request.audience_ids, request.user_input, request.user_id)
    return ProductRecommendResponse(products=products)

# ==================== 策略生成 ====================
@router.post("/strategy/generate", response_model=StrategyGenerateResponse)
async def strategy_generate(request: StrategyGenerateRequest):
    logger.info(f"策略生成请求，产品 {request.product_ids}, 客群规模 {len(request.audience_ids) if request.audience_ids else 0}")
    return run_generate_strategy(request.user_input, request.product_ids, request.audience_ids, request.user_id)

# ==================== 策略执行 ====================
@router.post("/execution/optimize", response_model=ExecutionOptimizeResponse)
async def execution_optimize(request: ExecutionOptimizeRequest):
    logger.info(f"执行优化请求，策略 {request.strategy_id}")
    return run_optimize_execution(request.user_input, request.product_ids, request.strategy_id, request.audience_ids, request.user_id)

# ==================== 效果评估 ====================
@router.post("/evaluation", response_model=EvaluationResponse)
async def evaluation(request: EvaluationRequest):
    logger.info(f"效果评估请求，策略 {request.strategy_id}")
    return run_evaluate_strategy(request.strategy_id, request.user_id)

# ==================== 策略发布 ====================
@router.post("/publish", response_model=MessageResponse)
async def publish_strategy(request: PublishRequest, db: Session = Depends(get_db)):
    """
    策略发布：将本次运营信息更新到运营用户清单表（ClickHouse）及各相关表
    """
    from app.services.clickhouse_service import client as ch_client
    logger.info(f"策略发布请求，策略 {request.strategy_id}, 产品 {request.product_ids}, 客群规模 {len(request.audience_ids)}")
    
    if not request.audience_ids:
        logger.warning("客群ID列表为空，发布终止")
        return MessageResponse(message="没有待运营用户，发布失败")
    
    # 获取当前月份和运营时间
    from datetime import datetime
    month_num = datetime.now().strftime("%Y%m")
    yy_date = datetime.now().strftime("%Y%m%d%H%M")
    
    # 安全获取 script_id 和 product_id
    script_id = request.script_ids[0] if request.script_ids else ""
    product_id = request.product_ids[0] if request.product_ids else ""
    
    batch_size = 1000
    total_inserted = 0
    try:
        for i in range(0, len(request.audience_ids), batch_size):
            batch = request.audience_ids[i:i+batch_size]
            for user_id in batch:
                ch_client.execute(
                    """
                    INSERT INTO user_strategies (month_num, user_id, city_id, yy_date, strategy_id, product_id, plan_id, script_id, is_yy)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (month_num, user_id, '', yy_date, request.strategy_id, product_id, request.plan_id, script_id, 1)
                )
                total_inserted += 1
        logger.info(f"策略发布完成，已写入 {total_inserted} 条运营记录")
        return MessageResponse(message=f"发布成功，已写入 {total_inserted} 条用户记录")
    except Exception as e:
        logger.error(f"策略发布失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")

# ==================== 全流程场景（LLMCompiler） ====================
@router.post("/flow/product_based")
async def flow_product_based(user_input: str, background_tasks: BackgroundTasks):
    """产品运营法全流程（异步执行）"""
    logger.info(f"产品运营法全流程启动: {user_input}")
    task = process_user_request.delay("product_based_flow", {"user_input": user_input})
    return {"task_id": task.id, "status": "processing"}

@router.post("/flow/audience_based")
# async def flow_audience_based(user_input: str, condition: str = "", background_tasks: BackgroundTasks):
async def flow_audience_based(user_input: str, condition: str = ""):
    """客群运营法全流程（异步执行）"""
    logger.info(f"客群运营法全流程启动: {user_input}, 条件: {condition}")
    task = process_user_request.delay("audience_based_flow", {"user_input": user_input, "condition": condition})
    return {"task_id": task.id, "status": "processing"}

# ==================== 工具接口 ====================
@router.get("/clickhouse/fields")
async def get_clickhouse_fields():
    """获取 user_behavior 表的所有字段（用于前端字段选择，过滤敏感字段）"""
    sql = "DESCRIBE TABLE user_behavior"
    result = execute_sql(sql)
    sensitive_fields = ['phone', 'phone_num', 'id_card', 'identity']
    fields = [row[0] for row in result['data'] if row[0] not in sensitive_fields]
    logger.info(f"获取 ClickHouse 字段: {fields}")
    return {"fields": fields}

@router.get("/products")
async def get_products(db: Session = Depends(get_db)):
    from app.models.product import Product
    products = db.query(Product).filter(Product.is_active == "TRUE").all()
    return {"products": [{"id": p.id, "name": p.name, "category": p.category, "price": p.price, "description": p.description, "applicable_scope": p.applicable_scope} for p in products]}

@router.get("/strategies")
async def get_strategies(db: Session = Depends(get_db)):
    from app.models.strategy import Strategy
    strategies = db.query(Strategy).filter(Strategy.is_active == "TRUE").all()
    return {"strategies": [{"id": s.id, "name": s.name, "category": s.category, "description": s.description} for s in strategies]}

@router.get("/health")
async def health():
    return {"status": "ok"}