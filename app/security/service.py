"""
Authentication service for user registration, login, token management, etc.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    User,
    RefreshToken,
    EmailVerificationToken,
    PasswordResetToken,
)
from app.security.password import hash_password, verify_password, check_password_strength
from app.security.jwt import create_access_token, create_refresh_token, verify_token
from app.security.token_utils import hash_token, verify_token_hash, create_token_with_prefix, extract_token_prefix
from app.security.cache import AuthCache
from app.security.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
    UserAlreadyExistsError,
    UserInactiveError,
    UserNotVerifiedError,
    AccountLockedError,
    TokenExpiredError,
    InvalidTokenError,
    RefreshTokenRevokedError,
)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize AuthService with database session and config."""
        self.db = db
        # Set some defaults since we don't have settings loaded currently
        self.MAX_FAILED_ATTEMPTS = 5
        self.LOCKOUT_DURATION_MINUTES = 15
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7
        self.EMAIL_VERIFICATION_EXPIRE_HOURS = 24
        self.PASSWORD_RESET_EXPIRE_HOURS = 1
    
    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
    ) -> tuple[User, str, str]:
        """
        Register a new user.
        
        Args:
            email: User work email
            password: Plain text password
            full_name: User full name
            
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            UserAlreadyExistsError: If user already exists
            ValueError: If password doesn't meet requirements
        """
        
        # Check if user already exists
        existing_user = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        existing = existing_user.scalar_one_or_none()
        if existing:
            # User exists in DB, ensure cache is in sync
            await AuthCache.set_user(existing)
            raise UserAlreadyExistsError(f"User with email {email} already exists")
        
        # Validate password strength
        is_valid, error_msg = check_password_strength(password)
        if not is_valid:
            raise ValueError(error_msg or "Password does not meet requirements")
        
        # Hash password
        password_hash = hash_password(password)
        
        # 1. Create users record
        user = User(
            email=email.lower(),
            name=full_name,
            password_hash=password_hash,
            is_active=True,
            is_verified=False,  # Email verification required
            failed_login_attempts=0
        )
        self.db.add(user)
        await self.db.flush()  # Get user.id without committing
        
        # Commit all records
        await self.db.commit()
        await self.db.refresh(user)
        
        # Cache user
        await AuthCache.set_user(user)
        
        # Generate tokens
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
        )
        
        plain_refresh_token, token_prefix = create_refresh_token()
        refresh_token_hash = hash_token(plain_refresh_token)  # Fast SHA-256 hashing
        
        # Store refresh token
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            token_prefix=token_prefix,  # For O(1) lookup
            expires_at=datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS),
            device_info=None
        )
        self.db.add(refresh_token)
        await self.db.commit()
        
        return user, access_token, plain_refresh_token
    
    async def login(
        self,
        email: str,
        password: str,
        device_info: Optional[Dict[str, Any]] = None
    ) -> tuple[User, str, str]:
        """
        Authenticate user and generate tokens.
        
        Args:
            email: User email
            password: Plain text password
            device_info: Optional device information (user agent, IP, etc.)
            
        Returns:
            Tuple of (user, access_token, refresh_token)
        """
        # Find user
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError(f"User with email {email} not found")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise AccountLockedError(
                f"Account is locked until {user.locked_until}",
                locked_until=user.locked_until.isoformat()
            )
        
        # Check if account is active
        if not user.is_active:
            raise UserInactiveError("User account is inactive")
        
        # Verify password
        if not verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if max attempts reached
            if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=self.LOCKOUT_DURATION_MINUTES
                )
            
            await self.db.commit()
            raise InvalidCredentialsError("Invalid email or password")
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        await self.db.commit()
        
        # Invalidate and refresh cache
        await AuthCache.invalidate_user(user.id)
        await AuthCache.set_user(user)
        
        # Generate tokens
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email
        )
        
        plain_refresh_token, token_prefix = create_refresh_token()
        refresh_token_hash = hash_token(plain_refresh_token)  # Fast SHA-256 hashing
        
        # Store refresh token
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            token_prefix=token_prefix,  # For O(1) lookup
            expires_at=datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS),
            device_info=str(device_info) if device_info else None
        )
        self.db.add(refresh_token)
        await self.db.commit()
        
        return user, access_token, plain_refresh_token
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate a new access token using a refresh token.
        """
        token_prefix = extract_token_prefix(refresh_token)
        
        result = await self.db.execute(
            select(RefreshToken).where(
                (RefreshToken.token_prefix == token_prefix) | (RefreshToken.token_prefix.is_(None)),
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
        candidate_tokens = result.scalars().all()
        
        matching_token = None
        for token in candidate_tokens:
            if verify_token_hash(refresh_token, token.token_hash):
                matching_token = token
                break
        
        if not matching_token:
            raise InvalidTokenError("Invalid refresh token")
        
        if matching_token.is_revoked or matching_token.revoked_at:
            raise RefreshTokenRevokedError("Refresh token has been revoked")
        
        if matching_token.expires_at < datetime.utcnow():
            raise TokenExpiredError("Refresh token has expired")
        
        # Get user
        user_result = await self.db.execute(
            select(User).where(User.id == matching_token.user_id)
        )
        user = user_result.scalar_one()
        
        if not user.is_active:
            raise UserInactiveError("User account is inactive")
        
        # Generate new access token
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email
        )
        
        return access_token
    
    async def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token (logout)."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
        all_tokens = result.scalars().all()
        
        for token in all_tokens:
            if verify_password(refresh_token, token.token_hash):
                token.is_revoked = True
                token.revoked_at = datetime.utcnow()
                await self.db.commit()
                return
    
    async def logout_all_devices(self, user_id: UUID) -> None:
        """Revoke all refresh tokens for a user (logout from all devices)."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            )
        )
        tokens = result.scalars().all()
        
        now = datetime.utcnow()
        for token in tokens:
            token.is_revoked = True
            token.revoked_at = now
            await AuthCache.invalidate_refresh_token(token.token_hash)
        
        await self.db.commit()
        await AuthCache.invalidate_user(user_id)
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
