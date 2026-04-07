from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.schemas import Repository, Scan
from app.models.pydantic_schemas import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryResponse,
    ScanCreate,
    ScanResponse,
    ScanStatus,
    TriggerType
)

router = APIRouter()


@router.post("/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repo: RepositoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new repository for scanning."""
    
    # Check if repository already exists
    result = await db.execute(
        select(Repository).where(Repository.url == repo.url)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository with this URL already exists"
        )
    
    # Create new repository
    db_repo = Repository(
        name=repo.name,
        url=repo.url,
        provider=repo.provider,
        branch=repo.branch,
        config=repo.config or {}
    )
    
    db.add(db_repo)
    await db.flush()
    await db.refresh(db_repo)
    
    return db_repo


@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all registered repositories."""
    
    query = select(Repository)
    
    if is_active is not None:
        query = query.where(Repository.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    repos = result.scalars().all()
    
    return list(repos)


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific repository by ID."""
    
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repo = result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    return repo


@router.put("/{repository_id}", response_model=RepositoryResponse)
async def update_repository(
    repository_id: int,
    repo_update: RepositoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update repository configuration."""
    
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repo = result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Update fields
    update_data = repo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(repo, field, value)
    
    await db.flush()
    await db.refresh(repo)
    
    return repo


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a repository and all associated data."""
    
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repo = result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    await db.delete(repo)
    await db.flush()


# Scan endpoints
@router.post("/{repository_id}/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def trigger_scan(
    repository_id: int,
    scan_data: ScanCreate,
    db: AsyncSession = Depends(get_db)
):
    """Trigger a new scan for a repository."""
    
    # Verify repository exists
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repo = result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Create scan record
    scan = Scan(
        repository_id=repository_id,
        trigger_type=scan_data.trigger_type,
        status=ScanStatus.PENDING
    )
    
    db.add(scan)
    await db.flush()
    await db.refresh(scan)
    
    # TODO: Queue scan job with Celery
    # from app.tasks import run_scan
    # run_scan.delay(scan.id)
    
    return scan


@router.get("/{repository_id}/scans", response_model=List[ScanResponse])
async def list_scans(
    repository_id: int,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List scans for a repository."""
    
    query = select(Scan).where(Scan.repository_id == repository_id)
    
    if status_filter:
        query = query.where(Scan.status == status_filter)
    
    query = query.order_by(Scan.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    scans = result.scalars().all()
    
    return list(scans)


@router.get("/{repository_id}/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(
    repository_id: int,
    scan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific scan."""
    
    result = await db.execute(
        select(Scan).where(
            Scan.id == scan_id,
            Scan.repository_id == repository_id
        )
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    return scan
