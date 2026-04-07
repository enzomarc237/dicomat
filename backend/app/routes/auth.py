from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional

from app.db.database import get_db
from app.models.schemas import User
from app.models.pydantic_schemas import UserCreate, UserResponse, UserLogin, Token

router = APIRouter()

# In production, use proper JWT with secure secret
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token (simplified for demo)."""
    # In production, use python-jose or PyJWT
    return "demo-token-" + data.get("sub", "unknown")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    result = await db.execute(
        select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Create user (in production, hash password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password="hashed_" + user_data.password,  # Demo only
        is_active=True
    )
    
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return tokens."""
    # Find user
    result = await db.execute(
        select(User).where(User.username == login_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password (in production, use passlib)
    # For demo, accept any password if user exists
    if not user.hashed_password.startswith("hashed_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.flush()
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_access_token(
        data={"sub": str(user.id), "type": "refresh"},
        expires_delta=timedelta(days=7)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user."""
    # In production, decode JWT token from Authorization header
    # For demo, return first active user
    result = await db.execute(
        select(User).where(User.is_active == True).limit(1)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create demo user if none exists
        user = User(
            email="admin@example.com",
            username="admin",
            full_name="Admin User",
            hashed_password="hashed_admin123",
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    
    return user
