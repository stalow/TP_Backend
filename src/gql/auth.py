"""
JWT authentication integration for GraphQL resolvers.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from django.conf import settings

from apps.accounts.models import User
from common.errors import TropicalCornerError
from common.tenancy import TenantContext, get_tenant_context


# def create_tokens(user: User) -> dict[str, str]:
#     """Create access and refresh tokens for a user."""
#     now = datetime.now(timezone.utc)

#     access_payload = {
#         "user_id": user.id,
#         "email": user.email,
#         "type": "access",
#         "iat": now,
#         "exp": now + timedelta(minutes=settings.JWT_EXPIRATION_DELTA_MINUTES),
#     }

#     refresh_payload = {
#         "user_id": user.id,
#         "type": "refresh",
#         "iat": now,
#         "exp": now + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS),
#     }

#     access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm="HS256")
#     refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET_KEY, algorithm="HS256")

#     return {
#         "accessToken": access_token,
#         "refreshToken": refresh_token,
#         "tokenType": "Bearer",
#     }


# def decode_token(token: str) -> dict[str, Any]:
#     """Decode and validate a JWT token."""
#     try:
#         return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
#     except jwt.ExpiredSignatureError:
#         raise TropicalCornerError("Token has expired", code="TOKEN_EXPIRED")
#     except jwt.InvalidTokenError as e:
#         raise TropicalCornerError(f"Invalid token: {e}", code="INVALID_TOKEN")


def get_user_from_request(request: Any) -> User | None:
    """Extract and validate user from request Authorization header."""

    return request.user if request.user.is_authenticated else None


def get_context_value(request: Any) -> dict[str, Any]:
    """
    Build the context dict for GraphQL resolvers.
    Contains request, user, and tenant context.
    """
    user = get_user_from_request(request)
    tenant_ctx: TenantContext | None = None

    if user is not None:
        tenant_ctx = get_tenant_context(user)

    return {
        "request": request,
        "user": user,
        "tenant_ctx": tenant_ctx,
    }


def require_auth(info: Any) -> User:
    """Require authentication in a resolver."""
    user = info.context.get("request").user
    if user is None:
        raise TropicalCornerError("Authentication required", code="UNAUTHENTICATED")
    return user


def require_tenant(info: Any) -> TenantContext:
    """Require authentication and an active organization."""
    require_auth(info)
    tenant_ctx = info.context.get("tenant_ctx")
    if tenant_ctx is None or tenant_ctx.organization is None:
        raise TropicalCornerError(
            "No active organization selected", code="NO_ACTIVE_ORG"
        )
    return tenant_ctx
