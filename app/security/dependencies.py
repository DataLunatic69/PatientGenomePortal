"""
FastAPI Dependencies for Authentication.
"""
from typing import Optional
from uuid import UUID
import logging

from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.models import User
from app.security.jwt import verify_token
from app.security.cache import AuthCache
from app.security.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
)

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


# ============================================================
# Core Authentication Dependencies
# ============================================================

async def get_user_from_token(user_id: str) -> Optional[User]:
    """Helper to get user from token (used by middleware)."""
    from app.database.session import get_async_session_context
    
    try:
        uid = UUID(user_id)
        cached_user = await AuthCache.get_user(uid)
        if cached_user:
            return User(
                id=uid,
                email=cached_user["email"],
                is_active=cached_user["is_active"],
                is_verified=cached_user["is_verified"],
            )
        
        async with get_async_session_context() as db:
            result = await db.execute(select(User).where(User.id == uid))
            return result.scalar_one_or_none()
    except Exception:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Raises:
        HTTPException 401: If not authenticated or token invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = await verify_token(credentials.credentials)
        user_id = UUID(payload.get("sub"))
        jti = payload.get("jti")
        
        # Check blacklist
        if jti and await AuthCache.is_token_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
        
        # Try cache first
        cached_user = await AuthCache.get_user(user_id)
        if cached_user:
            user = User(
                id=user_id,
                email=cached_user["email"],
                is_active=cached_user["is_active"],
                is_verified=cached_user["is_verified"],
                email_verified_at=cached_user.get("email_verified_at"),
                last_login_at=cached_user.get("last_login_at"),
                failed_login_attempts=cached_user.get("failed_login_attempts", 0),
                locked_until=cached_user.get("locked_until"),
            )
            return user
        
        # Fetch from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        await AuthCache.set_user(user)
        return user
        
    except (InvalidTokenError, TokenExpiredError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user (must be active)."""
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user (must be active AND verified)."""
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required")
    return current_user


async def get_optional_verified_user(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Optional[User]:
    """Get verified user if authenticated, None otherwise."""
    if current_user and current_user.is_active and current_user.is_verified:
        return current_user
    return None

