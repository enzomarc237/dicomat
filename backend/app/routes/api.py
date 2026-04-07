from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models import HealthStatus
from app.config import settings

router = APIRouter()


@router.get("/", response_model=dict)
async def get_api_info():
    """Get API information and version."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI-powered living documentation generator"
    }


@router.get("/health", response_model=HealthStatus)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check health of all services."""
    # Check database connection
    db_connected = False
    try:
        await db.execute("SELECT 1")
        db_connected = True
    except Exception:
        pass
    
    # Vector store connection would be checked here
    
    return HealthStatus(
        status="healthy" if db_connected else "degraded",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database_connected=db_connected,
        vector_store_connected=False  # TODO: Implement vector store check
    )
