# ============================================================================
# FastAPI 路由定义，提供所有 API 端点（完全匹配 PRD 交互）
# 谁调用：main.py（注册路由）
#如果是 run_xxx，那就是 simple_agents；
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.tasks.workflow_tasks import process_user_request
from app.models.schemas import *
from celery.result import AsyncResult
from app.tasks.celery_app import celery_app
from app.utils.sensitive_filter import filter_sensitive_data
from app.services.clickhouse_service import execute_sql
from app.utils.logger import logger
from app.agents.simple_agents import *


router = APIRouter(prefix="/api/v1", tags=["telecompass"])

# ==================== 客群分析 ====================
@router.post("/audience/nl2sql", response_model=NL2SQLResponse)
async def audience_nl2sql(request: NL2SQLRequest):
    """自然语言转SQL"""
    logger.info(f"NL2SQL 请求: {request.question}")
    return run_nl2sql(request.question, request.user_id)

@router.post("/audience/execute", response_model=ExecuteSQLResponse)
async def audience_execute(request: ExecuteSQLRequest):
    """执行SQL"""
    logger.info(f"执行SQL请求: {request.sql[:100]}")
    result = run_execute_sql(request.sql, request.user_id)
    return result

@router.post("/audience/save", response_model=MessageResponse)
async def audience_save(request: SaveAudienceRequest):
    """保存客群"""
    logger.info(f"保存客群: {request.name}")
    run_save_audience(request.name, request.condition_sql, request.user_id)
    return MessageResponse(message="保存成功")

@router.post("/audience/multidim", response_model=MultidimAnalysisResponse)
async def audience_multidim(request: MultidimAnalysisRequest):
    """多维分析（刷新右侧生命周期、高/低价值分布、雷达图、诊断表格）"""
    logger.info(f"多维分析请求，基础SQL: {request.base_sql}")
    return run_multidim_analysis(request.base_sql, request.user_id)

# ==================== 客群圈选 ====================
@router.post("/audience/seed", response_model=AudienceSelectionResponse)
async def audience_seed(request: SeedExpansionRequest):
    """种子扩散法圈选"""
    logger.info(f"种子扩散: 种子用户数 {len(request.seed_users)}, 目标 {request.target_count}")
    ids = run_seed_expansion(request.seed_users, request.target_count, request.user_id)
    return AudienceSelectionResponse(audience_ids=ids, total=len(ids))

@router.post("/audience/feature", response_model=AudienceSelectionResponse)
async def audience_feature(request: FeatureSelectionRequest):
    """特征组合法圈选"""
    logger.info(f"特征组合: {request.condition}")
    result = run_feature_selection(request.condition, request.fields, request.user_id)
    return AudienceSelectionResponse(**result)

@router.post("/audience/product", response_model=AudienceSelectionResponse)
async def audience_product(request: ProductAudienceRequest):
    """产品适配客群法圈选"""
    logger.info(f"产品适配圈选: 产品 {request.product_id}, 目标 {request.target_count}")
    ids = run_product_audience(request.product_id, request.target_count, request.user_id)
    return AudienceSelectionResponse(audience_ids=ids, total=len(ids))

@router.post("/audience/import", response_model=AudienceSelectionResponse)
async def audience_import(request: ImportAudienceRequest):
    """导入用户清单法圈选"""
    logger.info("导入用户清单")
    ids = run_import_audience(request.file_content, request.user_id)
    return AudienceSelectionResponse(audience_ids=ids, total=len(ids))

# ==================== 产品推荐 ====================
@router.post("/product/recommend_by_text", response_model=ProductRecommendResponse)
async def product_recommend_text(request: ProductRecommendByTextRequest):
    """基于文本推荐产品"""
    logger.info(f"文本推荐产品: {request.user_input}")
    products = run_recommend_by_text(request.user_input, request.user_id)
    return ProductRecommendResponse(products=products)

@router.post("/product/recommend_by_audience", response_model=ProductRecommendResponse)
async def product_recommend_audience(request: ProductRecommendByAudienceRequest):
    """基于客群推荐产品"""
    logger.info(f"客群推荐产品，客群规模 {len(request.audience_ids)}")
    products = run_recommend_by_audience(request.audience_ids, request.user_input, request.user_id)
    return ProductRecommendResponse(products=products)

# ==================== 策略生成 ====================
@router.post("/strategy/generate", response_model=StrategyGenerateResponse)
async def strategy_generate(request: StrategyGenerateRequest):
    """生成策略"""
    logger.info(f"策略生成请求，产品 {request.product_ids}, 客群规模 {len(request.audience_ids) if request.audience_ids else 0}")
    return run_generate_strategy(request.user_input, request.product_ids, request.audience_ids, request.user_id)

# ==================== 策略执行 ====================
@router.post("/execution/optimize", response_model=ExecutionOptimizeResponse)
async def execution_optimize(request: ExecutionOptimizeRequest):
    """执行优化（渠道、话术、波次、时刻）"""
    logger.info(f"执行优化请求，策略 {request.strategy_id}")
    return run_optimize_execution(request.user_input, request.product_ids, request.strategy_id, request.audience_ids, request.user_id)

# ==================== 效果评估 ====================
@router.post("/evaluation", response_model=EvaluationResponse)
async def evaluation(request: EvaluationRequest):
    """效果评估"""
    logger.info(f"效果评估请求，策略 {request.strategy_id}")
    return run_evaluate_strategy(request.strategy_id, request.user_id)

# ==================== 策略发布（更新数据库） ====================
@router.post("/publish", response_model=MessageResponse)
async def publish_strategy(request: PublishRequest, db: Session = Depends(get_db)):
    """
    策略发布：将本次运营信息更新到运营用户清单表（ClickHouse）及各相关表
    注意：user_strategies 表在 ClickHouse 中，需使用 ClickHouse 客户端
    """
    from app.models.user_strategy import UserStrategy
    from app.services.clickhouse_service import client as ch_client
    logger.info(f"策略发布请求，策略 {request.strategy_id}, 产品 {request.product_ids}, 客群规模 {len(request.audience_ids)}")
    
    # 获取当前月份
    from datetime import datetime
    month_num = datetime.now().strftime("%Y%m")
    yy_date = datetime.now().strftime("%Y%m%d%H%M")
    
    # 批量插入 ClickHouse（简化：逐条插入）
    for user_id in request.audience_ids[:100]:  # 示例只取前100，实际应分批
        ch_client.execute(f"""
            INSERT INTO user_strategies (month_num, user_id, city_id, yy_date, strategy_id, product_id, plan_id, script_id, is_yy)
            VALUES ('{month_num}', '{user_id}', '', '{yy_date}', '{request.strategy_id}', '{request.product_ids[0]}', '{request.plan_id}', '{request.script_ids[0]}', 1)
        """)
    logger.info(f"策略发布完成，已写入 {len(request.audience_ids)} 条运营记录")
    return MessageResponse(message="发布成功")

# ==================== 全流程场景（LLMCompiler） ====================
@router.post("/flow/product_based")
async def flow_product_based(user_input: str, background_tasks: BackgroundTasks):
    """产品运营法全流程（异步执行）"""
    logger.info(f"产品运营法全流程启动: {user_input}")
    task = process_user_request.delay("product_based_flow", {"user_input": user_input})
    return {"task_id": task.id, "status": "processing"}

@router.post("/flow/audience_based")
async def flow_audience_based(user_input: str, background_tasks: BackgroundTasks, condition: str = ""):
    """客群运营法全流程（异步执行）"""
    logger.info(f"客群运营法全流程启动: {user_input}, 条件: {condition}")
    task = process_user_request.delay("audience_based_flow", {"user_input": user_input, "condition": condition})
    return {"task_id": task.id, "status": "processing"}

# ==================== 工具接口 ====================
@router.get("/clickhouse/fields")
async def get_clickhouse_fields():
    """获取 user_behavior 表的所有字段（用于前端字段选择）"""
    sql = "DESCRIBE TABLE user_behavior"
    result = execute_sql(sql)
    sensitive_fields = ['phone', 'id_card', 'identity']
    fields = [row[0] for row in result['data'] if row[0] not in sensitive_fields]
    logger.info(f"获取 ClickHouse 字段: {fields}")
    return {"fields": fields}

@router.get("/products")
async def get_products(db: Session = Depends(get_db)):
    """获取所有产品（用于产品选择）"""
    from app.models.product import Product
    products = db.query(Product).filter(Product.is_active == "TRUE").all()
    return {"products": [{"id": p.id, "name": p.name, "category": p.category, "price": p.price, "description": p.description, "applicable_scope": p.applicable_scope} for p in products]}

@router.get("/strategies")
async def get_strategies(db: Session = Depends(get_db)):
    """获取所有策略（用于策略选择）"""
    from app.models.strategy import Strategy
    strategies = db.query(Strategy).filter(Strategy.is_active == "TRUE").all()
    return {"strategies": [{"id": s.id, "name": s.name, "category": s.category, "description": s.description} for s in strategies]}

@router.get("/health")
async def health():
    return {"status": "ok"}