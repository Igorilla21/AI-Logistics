from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, insert, join, select, update

from dynno_customs_api.models.domain import AuthSessionRecord, UserRecord
from dynno_customs_api.services.database import auth_sessions_table, get_engine, users_table


@dataclass(slots=True)
class StoredUserCredentials:
    user: UserRecord
    password_hash: str


@dataclass(slots=True)
class AuthenticatedSession:
    user: UserRecord
    session: AuthSessionRecord


class SqlAuthStore:
    def count_users(self) -> int:
        with get_engine().begin() as connection:
            return int(connection.execute(select(func.count()).select_from(users_table)).scalar_one())

    def save_user(self, user: UserRecord, password_hash: str) -> UserRecord:
        values = {
            "user_id": str(user.user_id),
            "email": user.email,
            "password_hash": password_hash,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login_at": user.last_login_at,
            "payload": user.model_dump(mode="json"),
        }

        with get_engine().begin() as connection:
            existing = connection.execute(
                select(users_table.c.user_id).where(users_table.c.user_id == str(user.user_id))
            ).scalar_one_or_none()

            if existing is None:
                connection.execute(insert(users_table).values(**values))
            else:
                connection.execute(update(users_table).where(users_table.c.user_id == str(user.user_id)).values(**values))

        return user

    def get_user_credentials_by_email(self, email: str) -> StoredUserCredentials | None:
        with get_engine().begin() as connection:
            row = connection.execute(
                select(users_table.c.payload, users_table.c.password_hash).where(users_table.c.email == email)
            ).one_or_none()

        if row is None:
            return None

        return StoredUserCredentials(
            user=UserRecord.model_validate(row.payload),
            password_hash=row.password_hash,
        )

    def update_last_login(self, user_id: UUID, logged_in_at: datetime) -> UserRecord | None:
        with get_engine().begin() as connection:
            row = connection.execute(
                select(users_table.c.payload, users_table.c.password_hash).where(users_table.c.user_id == str(user_id))
            ).one_or_none()

        if row is None:
            return None

        user = UserRecord.model_validate(row.payload).model_copy(
            update={
                "last_login_at": logged_in_at,
                "updated_at": logged_in_at,
            }
        )
        self.save_user(user, row.password_hash)
        return user

    def save_session(self, session: AuthSessionRecord, token_hash: str) -> AuthSessionRecord:
        values = {
            "session_id": str(session.session_id),
            "user_id": str(session.user_id),
            "token_hash": token_hash,
            "created_at": session.created_at,
            "expires_at": session.expires_at,
            "revoked_at": session.revoked_at,
            "payload": session.model_dump(mode="json"),
        }

        with get_engine().begin() as connection:
            existing = connection.execute(
                select(auth_sessions_table.c.session_id).where(auth_sessions_table.c.session_id == str(session.session_id))
            ).scalar_one_or_none()

            if existing is None:
                connection.execute(insert(auth_sessions_table).values(**values))
            else:
                connection.execute(
                    update(auth_sessions_table)
                    .where(auth_sessions_table.c.session_id == str(session.session_id))
                    .values(**values)
                )

        return session

    def get_authenticated_session(self, token_hash: str) -> AuthenticatedSession | None:
        statement = (
            select(
                users_table.c.payload.label("user_payload"),
                auth_sessions_table.c.payload.label("session_payload"),
            )
            .select_from(join(auth_sessions_table, users_table, auth_sessions_table.c.user_id == users_table.c.user_id))
            .where(auth_sessions_table.c.token_hash == token_hash)
        )

        with get_engine().begin() as connection:
            row = connection.execute(statement).one_or_none()

        if row is None:
            return None

        return AuthenticatedSession(
            user=UserRecord.model_validate(row.user_payload),
            session=AuthSessionRecord.model_validate(row.session_payload),
        )

    def revoke_session(self, session_id: UUID, revoked_at: datetime) -> AuthSessionRecord | None:
        with get_engine().begin() as connection:
            row = connection.execute(
                select(auth_sessions_table.c.payload, auth_sessions_table.c.token_hash).where(
                    auth_sessions_table.c.session_id == str(session_id)
                )
            ).one_or_none()

        if row is None:
            return None

        session = AuthSessionRecord.model_validate(row.payload).model_copy(update={"revoked_at": revoked_at})
        self.save_session(session, row.token_hash)
        return session

    def clear(self) -> None:
        with get_engine().begin() as connection:
            connection.execute(delete(auth_sessions_table))
            connection.execute(delete(users_table))


auth_store = SqlAuthStore()
