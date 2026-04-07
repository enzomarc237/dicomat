from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class Repository(Base):
    """Repository model for tracked code repositories."""
    
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False)
    provider = Column(String(50))  # github, gitlab, bitbucket
    branch = Column(String(255), default="main")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scan_at = Column(DateTime, nullable=True)
    
    # Relationships
    scans = relationship("Scan", back_populates="repository", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="repository", cascade="all, delete-orphan")
    
    # Configuration (stored as JSON)
    config = Column(JSON, default=dict)  # scan paths, exclusions, etc.


class Scan(Base):
    """Scan job model for tracking repository scans."""
    
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    trigger_type = Column(String(50))  # manual, scheduled, webhook
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    files_scanned = Column(Integer, default=0)
    documents_generated = Column(Integer, default=0)
    
    # Relationships
    repository = relationship("Repository", back_populates="scans")


class Document(Base):
    """Generated documentation model."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True)
    
    # Document metadata
    title = Column(String(512), nullable=False)
    slug = Column(String(512), nullable=False, index=True)
    doc_type = Column(String(50))  # api, class, function, config, example
    path = Column(String(1024))  # Source file path
    language = Column(String(50))  # python, javascript, etc.
    
    # Content
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Markdown content
    examples = Column(JSON, default=list)  # List of usage examples
    
    # Vector embedding reference
    embedding_id = Column(String(255), nullable=True)
    
    # Metadata
    version = Column(String(50), nullable=True)
    is_latest = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="documents")
    scan = relationship("Scan")
    
    # Indexes
    __table_args__ = (
        # Composite index for latest documents
        # Add via migrations
    )


class User(Base):
    """User model for authentication and access control."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Null for OAuth users
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    provider = Column(String(50))  # local, github, gitlab
    provider_id = Column(String(255), nullable=True)
    avatar_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    repositories = relationship("UserRepository", back_populates="user", cascade="all, delete-orphan")


class UserRepository(Base):
    """Many-to-many relationship between users and repositories."""
    
    __tablename__ = "user_repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    role = Column(String(50), default="viewer")  # viewer, editor, admin
    granted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="repositories")


class SearchQuery(Base):
    """Model for tracking search queries and analytics."""
    
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(512), nullable=False)
    results_count = Column(Integer, default=0)
    clicked_document_id = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Index for analytics
    __table_args__ = (
        # Add via migrations
    )
