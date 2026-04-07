from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""
    
    # Application
    APP_NAME: str = "DocuMate AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/documate"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Vector Search (Weaviate or Pinecone)
    VECTOR_DB_PROVIDER: str = "weaviate"  # weaviate, pinecone
    WEAVIATE_URL: str = "http://localhost:8080"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    
    # AI/ML
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    MAX_EMBEDDING_BATCH_SIZE: int = 32
    
    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Git & Scanning
    SCAN_WORKDIR: str = "/tmp/documate-scans"
    MAX_REPO_SIZE_MB: int = 500
    SUPPORTED_LANGUAGES: List[str] = ["python", "javascript", "typescript", "go", "java"]
    SUPPORTED_CONFIGS: List[str] = [".env", "docker-compose.yml", "docker-compose.yaml", 
                                     "k8s", "terraform", ".tf"]
    
    # Redaction
    ENABLE_REDACTION: bool = True
    CUSTOM_REDACTION_PATTERNS: List[str] = []
    
    # Storage
    STORAGE_PROVIDER: str = "local"  # local, s3
    STORAGE_PATH: str = "/app/storage"
    S3_BUCKET: Optional[str] = None
    S3_REGION: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    
    # Authentication
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITLAB_CLIENT_ID: Optional[str] = None
    GITLAB_CLIENT_SECRET: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json, console
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
