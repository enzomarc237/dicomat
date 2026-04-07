from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db.database import get_db
from app.models.schemas import Document
from app.models.pydantic_schemas import (
    DocumentResponse,
    DocumentType
)

router = APIRouter()


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    repository_id: Optional[int] = None,
    doc_type: Optional[DocumentType] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all generated documentation."""
    
    stmt = select(Document).where(Document.is_latest == True)
    
    if repository_id:
        stmt = stmt.where(Document.repository_id == repository_id)
    
    if doc_type:
        stmt = stmt.where(Document.doc_type == doc_type.value)
    
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    return list(documents)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document by ID."""
    
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return doc


@router.get("/slug/{slug:path}", response_model=DocumentResponse)
async def get_document_by_slug(
    slug: str,
    repository_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get a document by its slug (URL-friendly identifier)."""
    
    stmt = select(Document).where(
        Document.slug == slug,
        Document.is_latest == True
    )
    
    if repository_id:
        stmt = stmt.where(Document.repository_id == repository_id)
    
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return doc
