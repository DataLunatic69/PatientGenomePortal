from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    name: str = Field(default="", max_length=255)
    
    # Auth fields
    password_hash: str = Field()
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    email_verified_at: Optional[datetime] = Field(default=None)
    last_login_at: Optional[datetime] = Field(default=None)
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.utcnow()
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.utcnow()
    )

    # relationships
    dna_files: List["DnaFile"] = Relationship(back_populates="user")
    
    # Auth Relationships stringified as they are mapped in other files
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user", cascade_delete=True)
    password_reset_tokens: List["PasswordResetToken"] = Relationship(back_populates="user", cascade_delete=True)
    email_verification_tokens: List["EmailVerificationToken"] = Relationship(back_populates="user", cascade_delete=True)


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(index=True, unique=True)
    token_prefix: Optional[str] = Field(index=True)
    expires_at: datetime = Field()
    is_revoked: bool = Field(default=False)
    revoked_at: Optional[datetime] = Field(default=None)
    device_info: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    
    user: User = Relationship(back_populates="refresh_tokens")


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(index=True, unique=True)
    token_prefix: Optional[str] = Field(index=True)
    expires_at: datetime = Field()
    used_at: Optional[datetime] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    
    user: User = Relationship(back_populates="password_reset_tokens")


class EmailVerificationToken(SQLModel, table=True):
    __tablename__ = "email_verification_tokens"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(index=True, unique=True)
    token_prefix: Optional[str] = Field(index=True)
    expires_at: datetime = Field()
    verified_at: Optional[datetime] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    
    user: User = Relationship(back_populates="email_verification_tokens")

