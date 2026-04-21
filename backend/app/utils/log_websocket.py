# ============================================================================
# 文件功能：WebSocket 日志广播服务，将日志推送给所有前端连接
# 谁调用它：main.py 启动时初始化；logger 配置中调用
# 它调用谁：websockets, loguru, asyncio
# ============================================================================
import asyncio
import json
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

class LogWebSocketManager:
    """管理所有 WebSocket 连接，并广播日志消息"""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.loop = asyncio.get_event_loop()

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"日志 WebSocket 客户端连接，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """移除断开连接"""
        self.active_connections.discard(websocket)
        logger.info(f"日志 WebSocket 客户端断开，剩余连接: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """向所有连接的客户端广播日志消息"""
        if not self.active_connections:
            return
        data = json.dumps(message)
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(data)
            except Exception as e:
                logger.error(f"发送日志失败: {e}")
                self.disconnect(connection)

# 全局单例
ws_manager = LogWebSocketManager()

def log_to_websocket(record: dict):
    """loguru 的 sink 函数，将日志消息发送到 WebSocket"""
    # 只发送 INFO 及以上级别的日志（避免过多 DEBUG）
    if record["level"].name in ["INFO", "WARNING", "ERROR", "CRITICAL"]:
        # 构造可读的日志消息
        message = {
            "time": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": record["level"].name,
            "file": f"{record['file'].name}:{record['line']}",
            "function": record["function"],
            "message": str(record["message"]),
        }
        # 异步广播（因为 loguru 是同步调用，需要运行在事件循环中）
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast(message),
            ws_manager.loop
        )