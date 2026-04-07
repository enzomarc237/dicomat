from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog

from app.config import settings
from app.routes import api, scans, search, docs, auth
from app.db import database


# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(getattr(structlog, settings.LOG_LEVEL.upper())),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("Starting DocuMate AI", version=settings.APP_VERSION)
    
    # Initialize database
    await database.connect()
    logger.info("Database connection established")
    
    # Initialize vector search
    # from app.search.vector_store import init_vector_store
    # await init_vector_store()
    # logger.info("Vector store initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DocuMate AI")
    await database.disconnect()
    logger.info("Database connection closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered living documentation generator for internal APIs, configs, and libraries",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security middleware
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.documate.ai", "documate.ai"]
        )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger = structlog.get_logger()
        await logger.info("request_started", method=request.method, path=request.url.path)
        response = await call_next(request)
        await logger.info("request_completed", status_code=response.status_code)
        return response
    
    # Include routers
    app.include_router(api.router, prefix="/api/v1", tags=["api"])
    app.include_router(scans.router, prefix="/api/v1/scans", tags=["scans"])
    app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
    app.include_router(docs.router, prefix="/api/v1/docs", tags=["docs"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    
    # Root redirect to docs
    @app.get("/")
    async def root_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/api/docs")
    
    return app


# Create app instance
app = create_app()
