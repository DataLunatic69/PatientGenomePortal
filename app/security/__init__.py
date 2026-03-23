"""
Authentication module.
Handles user authentication, JWT tokens, and password management.
"""
from .password import verify_password, hash_password
from .jwt import create_access_token, create_refresh_token, verify_token, decode_token
from .token_utils import hash_token, verify_token_hash, create_token_with_prefix, extract_token_prefix
from .cache import AuthCache, CacheKeys, CacheTTL
from .service import AuthService
from .schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    TokenResponse,
    UserResponse,
    AuthResponse,
    MessageResponse,
    ErrorResponse,
)
# FastAPI Dependencies (from dependencies.py)
from .dependencies import (
    # Core auth
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_optional_current_user,
    get_optional_verified_user,
)

from .exceptions import (
    AuthenticationError,
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

__all__ = [
    # Password utilities
    "verify_password",
    "hash_password",
    # JWT utilities
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "decode_token",
    # Token utilities (fast hashing)
    "hash_token",
    "verify_token_hash",
    "create_token_with_prefix",
    "extract_token_prefix",
    # Cache
    "AuthCache",
    "CacheKeys",
    "CacheTTL",
    # Service
    "AuthService",
    # Schemas
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "LogoutRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "VerifyEmailRequest",
    "ResendVerificationRequest",
    "TokenResponse",
    "UserResponse",
    "AuthResponse",
    "MessageResponse",
    "ErrorResponse",
    # Core Auth Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_verified_user",
    "get_optional_current_user",
    "get_optional_verified_user",
    # Exceptions
    "AuthenticationError",
    "InvalidCredentialsError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "UserInactiveError",
    "UserNotVerifiedError",
    "AccountLockedError",
    "TokenExpiredError",
    "InvalidTokenError",
    "RefreshTokenRevokedError",
]
