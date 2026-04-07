from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TriggerType(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"


class DocumentType(str, Enum):
    API = "api"
    CLASS = "class"
    FUNCTION = "function"
    CONFIG = "config"
    EXAMPLE = "example"
    MODULE = "module"


# Repository Schemas
class RepositoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1)
    provider: str = Field(default="github")
    branch: str = Field(default="main", max_length=255)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    branch: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class RepositoryResponse(RepositoryBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_scan_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Scan Schemas
class ScanBase(BaseModel):
    trigger_type: TriggerType = Field(default=TriggerType.MANUAL)


class ScanCreate(ScanBase):
    repository_id: int


class ScanResponse(ScanBase):
    id: int
    repository_id: int
    status: ScanStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    files_scanned: int = 0
    documents_generated: int = 0
    
    class Config:
        from_attributes = True


class ScanProgress(BaseModel):
    scan_id: int
    status: ScanStatus
    progress: float = Field(ge=0, le=100)
    current_file: Optional[str] = None
    files_processed: int = 0
    total_files: Optional[int] = None


# Document Schemas
class ExampleUsage(BaseModel):
    code: str
    file_path: str
    line_number: int
    context: Optional[str] = None
    is_redacted: bool = False


class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    slug: str = Field(..., min_length=1, max_length=512)
    doc_type: DocumentType
    path: Optional[str] = None
    language: Optional[str] = None
    summary: Optional[str] = None


class DocumentCreate(DocumentBase):
    content: str
    examples: Optional[List[ExampleUsage]] = Field(default_factory=list)
    repository_id: int
    scan_id: Optional[int] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    examples: Optional[List[ExampleUsage]] = None
    is_latest: Optional[bool] = None


class DocumentResponse(DocumentBase):
    id: int
    repository_id: int
    scan_id: Optional[int] = None
    content: str
    examples: List[ExampleUsage] = Field(default_factory=list)
    embedding_id: Optional[str] = None
    version: Optional[str] = None
    is_latest: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentSearchResult(DocumentBase):
    id: int
    score: float
    snippet: str
    repository_name: str
    file_path: Optional[str] = None
    
    class Config:
        from_attributes = True


# Search Schemas
class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=512)
    repository_ids: Optional[List[int]] = None
    doc_types: Optional[List[DocumentType]] = None
    languages: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResponse(BaseModel):
    query: str
    results: List[DocumentSearchResult]
    total: int
    took_ms: int


# User Schemas
class UserBase(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=1, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    provider: str
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # user id
    exp: datetime
    type: str = "access"


# Analytics Schemas
class SearchAnalytics(BaseModel):
    total_searches: int
    zero_result_searches: int
    average_results: float
    top_queries: List[str]
    recent_searches: List[SearchQuery]


# Health Check Schema
class HealthStatus(BaseModel):
    status: str
    version: str
    environment: str
    database_connected: bool = False
    vector_store_connected: bool = False


# Webhook Schemas
class WebhookPayload(BaseModel):
    event: str
    repository: str
    ref: str
    commits: Optional[List[Dict[str, Any]]] = None
