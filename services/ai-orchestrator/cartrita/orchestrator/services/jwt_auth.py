# Cartrita AI OS - JWT Authentication Service
# Secure JWT-based authentication with proper token management

"""
JWT Authentication service for Cartrita AI OS.
Provides secure token-based authentication with proper validation and rate limiting.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel


class TokenData(BaseModel):
    """JWT token data model."""
    user_id: str
    permissions: list[str] = []
    issued_at: datetime
    expires_at: datetime


class JWTManager:
    """JWT token manager with secure defaults."""

    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Rate limiting storage (in production, use Redis)
        self._rate_limit_storage: Dict[str, list] = {}

    def create_access_token(self, user_id: str, permissions: list[str] = None) -> str:
        """Create a JWT access token."""
        if permissions is None:
            permissions = []

        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "permissions": permissions,
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
            "type": "access"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
            "type": "refresh"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing subject",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Check token type
            token_type = payload.get("type", "access")
            if token_type not in ["access", "refresh"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            permissions = payload.get("permissions", [])
            iat = datetime.fromtimestamp(payload.get("iat", 0), tz=timezone.utc)
            exp = datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc)

            return TokenData(
                user_id=user_id,
                permissions=permissions,
                issued_at=iat,
                expires_at=exp
            )

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def check_rate_limit(self, identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if request is within rate limits."""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)

        # Clean old attempts
        if identifier in self._rate_limit_storage:
            self._rate_limit_storage[identifier] = [
                attempt_time for attempt_time in self._rate_limit_storage[identifier]
                if attempt_time > window_start
            ]
        else:
            self._rate_limit_storage[identifier] = []

        # Check if under limit
        if len(self._rate_limit_storage[identifier]) >= max_attempts:
            return False

        # Record this attempt
        self._rate_limit_storage[identifier].append(now)
        return True


# Global JWT manager instance
jwt_manager = JWTManager()

# FastAPI security scheme
security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Get current authenticated user from JWT token.
    Includes rate limiting and proper error handling.
    """
    # Rate limiting by IP
    client_ip = request.client.host if request.client else "unknown"

    if not jwt_manager.check_rate_limit(f"auth:{client_ip}", max_attempts=10, window_minutes=5):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again later.",
            headers={"Retry-After": "300"}
        )

    # Verify token
    token_data = jwt_manager.verify_token(credentials.credentials)

    # Check if token is expired (additional check)
    if token_data.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


async def require_permission(permission: str):
    """Dependency factory for permission-based access control."""
    async def permission_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return current_user
    return permission_checker


# Backwards compatibility with existing API key auth
async def verify_api_key_or_jwt(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Verify either API key (legacy) or JWT token.
    This provides backwards compatibility during migration.
    """
    # Check for JWT token first
    if credentials:
        try:
            token_data = await get_current_user(request, credentials)
            return token_data.user_id
        except HTTPException:
            pass  # Fall back to API key check

    # Fall back to API key authentication
    from .auth import verify_api_key
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        # Create a mock dependencies object for the old function
        class MockDeps:
            def __init__(self, key):
                self.key = key

        try:
            return await verify_api_key(api_key_header)
        except HTTPException:
            pass

    # Neither authentication method worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid authentication required (JWT token or API key)",
        headers={"WWW-Authenticate": "Bearer"},
    )
