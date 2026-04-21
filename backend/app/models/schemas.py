# ============================================================================
# 文件功能：Pydantic 模型，用于 API 请求和响应的数据校验
# 谁调用它：routes.py（作为请求/响应类型）
# 它调用谁：无
# ============================================================================
# ============================================================================
# Pydantic 模型，用于 API 请求和响应的数据校验
# ============================================================================
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class MessageResponse(BaseModel):
    message: str

# 客群分析
class NL2SQLRequest(BaseModel):
    question: str
    user_id: str = "system"


class NL2SQLResponse(BaseModel):
    sql: str

class ExecuteSQLRequest(BaseModel):
    sql: str
    user_id: str = "system"


class ExecuteSQLResponse(BaseModel):
    columns: List[str]
    data: List[List[Any]]
    total: int

class SaveAudienceRequest(BaseModel):
    name: str
    condition_sql: str
    user_id: str = "system"

class MultidimAnalysisRequest(BaseModel):
    base_sql: str   # "FROM user_behavior WHERE ..."
    user_id: str = "system"

class MultidimAnalysisResponse(BaseModel):
    lifecycle: List[Dict]
    high_low_dist: Dict
    radar: Dict
    diagnosis_table: List[Dict]

# 客群圈选
class SeedExpansionRequest(BaseModel):
    seed_users: List[str]
    target_count: int
    user_id: str = "system"

class FeatureSelectionRequest(BaseModel):
    condition: Optional[str] = None
    fields: Optional[List[str]] = None
    audience_name: Optional[str] = None   # 新增
    user_id: str = "system"

class ProductAudienceRequest(BaseModel):
    product_id: str
    target_count: int
    user_id: str = "system"

class ImportAudienceRequest(BaseModel):
    file_content: str   # base64
    user_id: str = "system"

class AudienceSelectionResponse(BaseModel):
    audience_ids: List[str]
    total: int
    fields: Optional[List[str]] = None
    data: Optional[List[List[Any]]] = None

# 产品推荐
class ProductRecommendByTextRequest(BaseModel):
    user_input: str
    user_id: str = "system"

class ProductRecommendByAudienceRequest(BaseModel):
    audience_ids: List[str]
    user_input: Optional[str] = None
    user_id: str = "system"

class ProductRecommendResponse(BaseModel):
    products: List[Dict]

# 策略生成
class StrategyGenerateRequest(BaseModel):
    user_input: str
    product_ids: List[str]
    audience_ids: Optional[List[str]] = None
    user_id: str = "system"

class StrategyDetail(BaseModel):
    name: str
    category: str
    description: str
    activity_desc: str
    charge_method: str
    rights_content: str
    valid_period: str
    conditions: str
    audience_scale: Optional[int] = None

class StrategyGenerateResponse(BaseModel):
    strategy_id: str
    detail: StrategyDetail

# 策略执行
class ExecutionOptimizeRequest(BaseModel):
    user_input: str
    product_ids: List[str]
    strategy_id: str
    audience_ids: Optional[List[str]] = None
    user_id: str = "system"

class ChannelScript(BaseModel):
    channel: str
    scripts: List[str]

class ExecutionOptimizeResponse(BaseModel):
    channels: List[ChannelScript]
    wave_count: int
    wave_interval_hours: int
    time_preference: Dict
    plan_id: str
    script_ids: List[str]

# 效果评估
class EvaluationRequest(BaseModel):
    strategy_id: str
    user_id: str = "system"

class EvaluationResponse(BaseModel):
    predicted_conversion_rate: float
    predicted_roi: float
    predicted_click_rate: float

# 策略发布
class PublishRequest(BaseModel):
    strategy_id: str
    product_ids: List[str]
    audience_ids: List[str]
    plan_id: str
    script_ids: List[str]
    user_id: str = "system"