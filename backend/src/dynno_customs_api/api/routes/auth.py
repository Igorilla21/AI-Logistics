from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from uuid import uuid4

from dynno_customs_api.api.dependencies import CurrentAuthSession
from dynno_customs_api.config import settings
from dynno_customs_api.models.api import (
    AuthBootstrapStatusResponse,
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthTokenResponse,
    UserResponse,
)
from dynno_customs_api.models.domain import AuthSessionRecord, UserRecord
from dynno_customs_api.services.auth_security import (
    build_session_expiry,
    generate_session_token,
    hash_password,
    hash_session_token,
    normalize_email,
    utc_now,
    verify_password,
)
from dynno_customs_api.services.auth_store import auth_store


router = APIRouter()


def _registration_is_open(*, has_users: bool) -> bool:
    return settings.auth_open_registration or not has_users


def _user_response(user: UserRecord) -> UserResponse:
    return UserResponse.model_validate(user.model_dump(mode="json"))


def _issue_auth_token(user: UserRecord, issued_at: datetime) -> AuthTokenResponse:
    raw_token = generate_session_token()
    session = AuthSessionRecord(
        session_id=uuid4(),
        user_id=user.user_id,
        created_at=issued_at,
        expires_at=build_session_expiry(issued_at),
    )
    auth_store.save_session(session, hash_session_token(raw_token))
    return AuthTokenResponse(
        access_token=raw_token,
        expires_at=session.expires_at,
        user=_user_response(user),
    )


@router.get("/bootstrap-status", response_model=AuthBootstrapStatusResponse)
def get_bootstrap_status() -> AuthBootstrapStatusResponse:
    has_users = auth_store.count_users() > 0
    return AuthBootstrapStatusResponse(
        has_users=has_users,
        registration_open=_registration_is_open(has_users=has_users),
    )


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthRegisterRequest) -> AuthTokenResponse:
    has_users = auth_store.count_users() > 0
    if not _registration_is_open(has_users=has_users):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Open registration is disabled for this workspace.",
        )

    try:
        email = normalize_email(payload.email)
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if auth_store.get_user_credentials_by_email(email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists.")

    full_name = payload.full_name.strip()
    if len(full_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name must be at least 2 non-space characters.",
        )

    now = utc_now()
    user = UserRecord(
        user_id=uuid4(),
        email=email,
        full_name=full_name,
        role="admin" if not has_users else "operator",
        is_active=True,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    auth_store.save_user(user, password_hash)
    return _issue_auth_token(user, issued_at=now)


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: AuthLoginRequest) -> AuthTokenResponse:
    try:
        email = normalize_email(payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    stored_user = auth_store.get_user_credentials_by_email(email)
    if stored_user is None or not verify_password(payload.password, stored_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not stored_user.user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive.")

    now = utc_now()
    user = auth_store.update_last_login(stored_user.user.user_id, now)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _issue_auth_token(user, issued_at=now)


@router.get("/me", response_model=UserResponse)
def me(auth_session: CurrentAuthSession) -> UserResponse:
    return _user_response(auth_session.user)


@router.post("/logout")
def logout(auth_session: CurrentAuthSession) -> dict[str, str]:
    auth_store.revoke_session(auth_session.session.session_id, utc_now())
    return {"status": "logged_out"}
