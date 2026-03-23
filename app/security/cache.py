"""
Authentication-specific caching utilities.
Using a simple in-memory stub for now since Redis is not configured in this app.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.database.models import User

logger = logging.getLogger(__name__)


# Cache key patterns
class CacheKeys:
    """Cache key patterns for authentication."""
    
    USER = "auth:user:{user_id}"
    TOKEN_BLACKLIST = "auth:token:blacklist:{jti}"
    REFRESH_TOKEN = "auth:refresh:{token_hash}"
    
    @staticmethod
    def user_key(user_id: UUID) -> str:
        """Get user cache key."""
        return CacheKeys.USER.format(user_id=str(user_id))
    
    @staticmethod
    def token_blacklist_key(jti: str) -> str:
        """Get token blacklist key."""
        return CacheKeys.TOKEN_BLACKLIST.format(jti=jti)
    
    @staticmethod
    def refresh_token_key(token_hash: str) -> str:
        """Get refresh token cache key."""
        return CacheKeys.REFRESH_TOKEN.format(token_hash=token_hash)


# Cache TTLs (in seconds)
class CacheTTL:
    """Cache TTL constants."""
    USER = 3600  # 1 hour
    REFRESH_TOKEN = 30 * 24 * 3600  # 30 days

# Dummy dictionary for in memory local cache. 
# Works only per-worker for simple dev mock.
_local_cache = {}


class AuthCache:
    """Authentication cache service."""
    
    @staticmethod
    async def get_user(user_id: UUID) -> Optional[Dict[str, Any]]:
        key = CacheKeys.user_key(user_id)
        return _local_cache.get(key)
    
    @staticmethod
    async def set_user(user: User, ttl: int = CacheTTL.USER) -> bool:
        key = CacheKeys.user_key(user.id)
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "email_verified_at": user.email_verified_at.isoformat() if user.email_verified_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
        _local_cache[key] = user_data
        return True
    
    @staticmethod
    async def invalidate_user(user_id: UUID) -> bool:
        key = CacheKeys.user_key(user_id)
        _local_cache.pop(key, None)
        return True
    
    @staticmethod
    async def is_token_blacklisted(jti: str) -> bool:
        key = CacheKeys.token_blacklist_key(jti)
        return key in _local_cache
    
    @staticmethod
    async def blacklist_token(jti: str, ttl: int) -> bool:
        key = CacheKeys.token_blacklist_key(jti)
        _local_cache[key] = {"blacklisted_at": datetime.utcnow().isoformat()}
        return True
    
    @staticmethod
    async def cache_refresh_token(token_hash: str, user_id: UUID, ttl: int = CacheTTL.REFRESH_TOKEN) -> bool:
        key = CacheKeys.refresh_token_key(token_hash)
        _local_cache[key] = {
            "user_id": str(user_id),
            "cached_at": datetime.utcnow().isoformat()
        }
        return True
    
    @staticmethod
    async def get_refresh_token(token_hash: str) -> Optional[Dict[str, Any]]:
        key = CacheKeys.refresh_token_key(token_hash)
        return _local_cache.get(key)
    
    @staticmethod
    async def invalidate_refresh_token(token_hash: str) -> bool:
        key = CacheKeys.refresh_token_key(token_hash)
        _local_cache.pop(key, None)
        return True
