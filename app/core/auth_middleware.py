"""Authentication middleware and JWT validation dependency for Supabase / Clerk in FastAPI."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

logger = logging.getLogger("auth_middleware")

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Supabase Auth Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://mock-project.supabase.co")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_AUDIENCE = os.getenv("SUPABASE_AUDIENCE", "authenticated")

# Whether authentication is strictly required in this environment (defaults to False in development/testing)
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() in ("true", "1", "yes")

# HTTP Bearer security scheme
security_scheme = HTTPBearer(auto_error=False)


# -----------------------------------------------------------------------------
# User Schema
# -----------------------------------------------------------------------------


class AuthenticatedUser(BaseModel):
    """User identity extracted from verified Supabase / Clerk JWT."""

    user_id: str = Field(..., description="Unique Supabase user identifier (sub)")
    email: str = Field(default="user@example.com", description="User email address")
    role: str = Field(default="authenticated", description="User role")
    aud: Optional[str] = Field(default="authenticated", description="JWT audience")
    user_metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom user metadata")
    app_metadata: Dict[str, Any] = Field(default_factory=dict, description="Application metadata")

    @property
    def is_authenticated(self) -> bool:
        return bool(self.user_id)


# Fallback development user for local offline testing
MOCK_DEV_USER = AuthenticatedUser(
    user_id="usr_dev_001",
    email="developer@example.com",
    role="authenticated",
    user_metadata={"full_name": "Dev Engineer", "plan": "Pro Creator"},
)


# -----------------------------------------------------------------------------
# Token Validation
# -----------------------------------------------------------------------------


def verify_jwt_token(token: str) -> AuthenticatedUser:
    """Validate a Supabase or standard RS256/HS256 JWT bearer token.

    Parameters
    ----------
    token : str
        The raw JWT string passed in the Authorization: Bearer <token> header.

    Returns
    -------
    AuthenticatedUser
        Parsed and validated user context.

    Raises
    ------
    HTTPException
        HTTP 401 if token is expired, invalid, or signature fails.
    """
    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Production Mode: Verify cryptographic signature if secret is provided
    if SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience=SUPABASE_AUDIENCE,
                options={"verify_exp": True, "verify_aud": True},
            )
            return AuthenticatedUser(
                user_id=str(payload.get("sub", "")),
                email=str(payload.get("email", "")),
                role=str(payload.get("role", "authenticated")),
                aud=str(payload.get("aud", "authenticated")),
                user_metadata=payload.get("user_metadata", {}),
                app_metadata=payload.get("app_metadata", {}),
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Supabase JWT has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as exc:
            logger.warning("Invalid Supabase JWT: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 2. Development / Testing Mode: Decode payload without signature verification if secret is not set
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return AuthenticatedUser(
            user_id=str(payload.get("sub", "usr_dev_001")),
            email=str(payload.get("email", "developer@example.com")),
            role=str(payload.get("role", "authenticated")),
            aud=str(payload.get("aud", "authenticated")),
            user_metadata=payload.get("user_metadata", {}),
            app_metadata=payload.get("app_metadata", {}),
        )
    except Exception as exc:
        if AUTH_REQUIRED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unable to parse token: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Graceful fallback in non-strict local test mode
        logger.debug("Falling back to local development mock user context: %s", exc)
        return MOCK_DEV_USER


# -----------------------------------------------------------------------------
# FastAPI Dependencies
# -----------------------------------------------------------------------------


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> AuthenticatedUser:
    """FastAPI dependency requiring a valid Bearer token for protected endpoints."""
    if not credentials:
        if not AUTH_REQUIRED:
            # In local development without auth enforced, permit fallback user
            return MOCK_DEV_USER

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header with Bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_jwt_token(credentials.credentials)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> Optional[AuthenticatedUser]:
    """FastAPI dependency for endpoints that support both authenticated and guest usage."""
    if not credentials:
        return None
    try:
        return verify_jwt_token(credentials.credentials)
    except HTTPException:
        return None
