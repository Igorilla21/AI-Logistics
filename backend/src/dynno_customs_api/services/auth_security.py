from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
from hmac import compare_digest
import secrets

from dynno_customs_api.config import settings


PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 310_000
PASSWORD_SALT_BYTES = 16
SESSION_TOKEN_BYTES = 32


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email:
        raise ValueError("Email address must contain '@'.")

    local_part, _, domain_part = email.partition("@")
    if not local_part or not domain_part or "." not in domain_part:
        raise ValueError("Email address must be valid.")

    return email


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")


def hash_password(password: str) -> str:
    validate_password_strength(password)
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations_raw, salt_hex, digest_hex = stored_hash.split("$", 3)
    except ValueError:
        return False

    if scheme != PASSWORD_SCHEME:
        return False

    try:
        iterations = int(iterations_raw)
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)
    except ValueError:
        return False

    actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return compare_digest(actual_digest, expected_digest)


def generate_session_token() -> str:
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC)


def build_session_expiry(created_at: datetime | None = None) -> datetime:
    issued_at = created_at or utc_now()
    return issued_at + timedelta(hours=settings.auth_token_ttl_hours)
