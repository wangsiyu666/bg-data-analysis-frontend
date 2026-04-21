# ============================================================================
# 文件功能：FastAPI 应用入口，注册路由，启动后台初始化
# 谁调用它：uvicorn 命令行
# 它调用谁：routes, vanna_service
# ============================================================================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utils.logger import logger
from app.services.vanna_service import init_vanna

app = FastAPI(title="TeleCompass", version="1.0")
# 添加 CORS 中间件，允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.on_event("startup")
async def startup():
    """应用启动时执行：初始化 Vanna（异步，不阻塞）"""
    logger.info("后端服务启动中...")
    import threading
    threading.Thread(target=init_vanna, daemon=True).start()
    logger.info("启动完成")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)