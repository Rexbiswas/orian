import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    try:
        from pydantic import BaseSettings
        SettingsConfigDict = dict
    except ImportError:
        class BaseSettings:
            pass
        SettingsConfigDict = dict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Orian AI Digital Brain"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    
    # File Storage Paths
    ORIAN_ROOT_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orian_storage"))
    PROJECTS_DIR: str = os.path.join(ORIAN_ROOT_DIR, "projects")
    DOCUMENTS_DIR: str = os.path.join(ORIAN_ROOT_DIR, "documents")
    MEDIA_DIR: str = os.path.join(ORIAN_ROOT_DIR, "media")
    GENERATED_DIR: str = os.path.join(ORIAN_ROOT_DIR, "generated")
    LOGS_DIR: str = os.path.join(ORIAN_ROOT_DIR, "logs")
    CACHE_DIR: str = os.path.join(ORIAN_ROOT_DIR, "cache")
    TEMP_DIR: str = os.path.join(ORIAN_ROOT_DIR, "temp")
    
    # SQLite
    SQLITE_DB_PATH: str = os.path.join(ORIAN_ROOT_DIR, "orian_core.db")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    
    # Qdrant
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    QDRANT_COLLECTION: str = "orian_memories"
    
    # LLM Models
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "local")  # openai, huggingface, local
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY", None)
    HUGGINGFACE_MODEL: str = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-2-7b-chat-hf")
    
    # Security Defaults
    DEFAULT_RISK_POLICY: str = "strict"  # strict, balanced, permissive
    REQUIRE_CONFIRMATION_FOR_MEDIUM_RISK: bool = True
    REQUIRE_CONFIRMATION_FOR_HIGH_RISK: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure directories exist
for path in [
    settings.ORIAN_ROOT_DIR,
    settings.PROJECTS_DIR,
    settings.DOCUMENTS_DIR,
    settings.MEDIA_DIR,
    settings.GENERATED_DIR,
    settings.LOGS_DIR,
    settings.CACHE_DIR,
    settings.TEMP_DIR,
]:
    os.makedirs(path, exist_ok=True)
