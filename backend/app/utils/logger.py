# ============================================================================
# 日志配置，程序运行时需要记录信息、警告、错误，方便调试和监控，使用 loguru 输出到控制台和文件
# 同时输出到控制台（彩色）和文件（滚动保存）。
# 支持不同级别：INFO, DEBUG, WARNING, ERROR。
# 每条日志自动包含时间戳、模块名、函数名、行号。
# ============================================================================
import sys
from loguru import logger

logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>", colorize=True)
logger.add("logs/telecompass_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days", level="DEBUG", encoding="utf-8")
__all__ = ["logger"]