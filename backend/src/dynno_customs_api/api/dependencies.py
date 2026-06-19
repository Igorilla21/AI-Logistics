from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dynno_customs_api.services.auth_security import hash_session_token, utc_now
from dynno_customs_api.services.auth_store import AuthenticatedSession, auth_store


bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_auth_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedSession:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise unauthorized("Authentication required.")

    auth_session = auth_store.get_authenticated_session(hash_session_token(credentials.credentials))
    if auth_session is None:
        raise unauthorized("Invalid or expired authentication token.")

    now = utc_now()
    if auth_session.session.revoked_at is not None or auth_session.session.expires_at <= now:
        raise unauthorized("Invalid or expired authentication token.")
    if not auth_session.user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive.")

    return auth_session


CurrentAuthSession = Annotated[AuthenticatedSession, Depends(get_current_auth_session)]
