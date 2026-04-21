import os
from dotenv import load_dotenv
from app.utils.logger import logger

load_dotenv()

class Settings:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "host.docker.internal")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "123456")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "telecompass")
    @property
    def SQLALCHEMY_DATABASE_URL(self):
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "host.docker.internal")
    CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 8123))
    REDIS_URL = os.getenv("REDIS_URL", "redis://host.docker.internal:6379/0")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen:7b-chat-q4_0")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
logger.info(f"配置加载完成: {settings}")