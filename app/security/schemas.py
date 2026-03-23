"""
Pydantic schemas for authentication requests and responses.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ====================
# Request Schemas
# ====================

class RegisterRequest(BaseModel):
    """User registration request."""
    # User fields
    email: EmailStr = Field(..., description="Work email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    full_name: str = Field(..., min_length=2, description="User full name")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "full_name": "James Peterson",
            }
        }
    )


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str = Field(..., description="Refresh token")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "abc123def456..."
            }
        }
    )


class LogoutRequest(BaseModel):
    """Logout request."""
    refresh_token: str = Field(..., description="Refresh token to revoke")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "abc123def456..."
            }
        }
    )


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr = Field(..., description="User email address")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class ResetPasswordRequest(BaseModel):
    """Reset password request."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "reset_token_abc123",
                "new_password": "NewSecurePass123!"
            }
        }
    )


class VerifyEmailRequest(BaseModel):
    """Email verification request."""
    token: str = Field(..., description="Email verification token")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "verification_token_abc123"
            }
        }
    )


class ResendVerificationRequest(BaseModel):
    """Resend email verification request."""
    email: EmailStr = Field(..., description="User email address")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


# ====================
# Response Schemas
# ====================

class TokenResponse(BaseModel):
    """Token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "abc123def456...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }
    )


class UserResponse(BaseModel):
    """User response."""
    id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User full name")
    is_active: bool = Field(..., description="Is user active")
    is_verified: bool = Field(..., description="Is email verified")
    email_verified_at: Optional[datetime] = Field(None, description="Email verification timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Authentication response with user and tokens."""
    user: UserResponse = Field(..., description="User information")
    tokens: TokenResponse = Field(..., description="Access and refresh tokens")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "name": "James Peterson",
                    "is_active": True,
                    "is_verified": False,
                    "created_at": "2025-01-01T00:00:00Z"
                },
                "tokens": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "abc123def456...",
                    "token_type": "bearer",
                    "expires_in": 1800
                }
            }
        }
    )


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str = Field(..., description="Response message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully"
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "InvalidCredentialsError",
                "message": "Invalid email or password",
                "detail": None
            }
        }
    )

