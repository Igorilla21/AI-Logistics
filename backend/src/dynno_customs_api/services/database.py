from __future__ import annotations

from pathlib import Path

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String, Table, create_engine
from sqlalchemy.engine import Engine

from dynno_customs_api.config import settings


metadata = MetaData()

document_packs_table = Table(
    "document_packs",
    metadata,
    Column("pack_id", String(36), primary_key=True),
    Column("status", String(64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, index=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSON, nullable=False),
)

document_files_table = Table(
    "document_files",
    metadata,
    Column("document_id", String(36), primary_key=True),
    Column("pack_id", String(36), ForeignKey("document_packs.pack_id", ondelete="CASCADE"), nullable=False, index=True),
    Column("uploaded_at", DateTime(timezone=True), nullable=False, index=True),
    Column("file_name", String(512), nullable=False),
    Column("stored_path", String(1024), nullable=False),
    Column("content_type", String(255), nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("payload", JSON, nullable=False),
)

ocr_document_results_table = Table(
    "ocr_document_results",
    metadata,
    Column("document_id", String(36), primary_key=True),
    Column("pack_id", String(36), ForeignKey("document_packs.pack_id", ondelete="CASCADE"), nullable=False, index=True),
    Column("created_at", DateTime(timezone=True), nullable=False, index=True),
    Column("status", String(32), nullable=False),
    Column("source_file_name", String(512), nullable=False),
    Column("payload", JSON, nullable=False),
)

normalized_documents_table = Table(
    "normalized_documents",
    metadata,
    Column("document_id", String(36), primary_key=True),
    Column("pack_id", String(36), ForeignKey("document_packs.pack_id", ondelete="CASCADE"), nullable=False, index=True),
    Column("document_type", String(128), nullable=False, index=True),
    Column("source_file_name", String(512), nullable=False),
    Column("extraction_status", String(64), nullable=False),
    Column("payload", JSON, nullable=False),
)

validation_reports_table = Table(
    "validation_reports",
    metadata,
    Column("report_id", String(36), primary_key=True),
    Column("pack_id", String(36), nullable=False, index=True),
    Column("generated_at", DateTime(timezone=True), nullable=False, index=True),
    Column("payload", JSON, nullable=False),
)

validation_results_table = Table(
    "validation_results",
    metadata,
    Column(
        "report_id",
        String(36),
        ForeignKey("validation_reports.report_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    ),
    Column("pack_id", String(36), nullable=False, index=True),
    Column("rule_code", String(16), primary_key=True, nullable=False, index=True),
    Column("status", String(32), nullable=False, index=True),
    Column("severity", String(32), nullable=False, index=True),
    Column("created_at", DateTime(timezone=True), nullable=False, index=True),
    Column("payload", JSON, nullable=False),
)

users_table = Table(
    "users",
    metadata,
    Column("user_id", String(36), primary_key=True),
    Column("email", String(320), nullable=False, unique=True, index=True),
    Column("password_hash", String(512), nullable=False),
    Column("full_name", String(255), nullable=False),
    Column("role", String(64), nullable=False, index=True),
    Column("is_active", Boolean, nullable=False, index=True),
    Column("created_at", DateTime(timezone=True), nullable=False, index=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("last_login_at", DateTime(timezone=True), nullable=True),
    Column("payload", JSON, nullable=False),
)

auth_sessions_table = Table(
    "auth_sessions",
    metadata,
    Column("session_id", String(36), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True),
    Column("token_hash", String(64), nullable=False, unique=True, index=True),
    Column("created_at", DateTime(timezone=True), nullable=False, index=True),
    Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
    Column("revoked_at", DateTime(timezone=True), nullable=True, index=True),
    Column("payload", JSON, nullable=False),
)

_engine: Engine | None = None
_engine_url: str | None = None


def _sqlite_connect_args(database_url: str) -> dict[str, bool]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _ensure_database_parent_dir(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return

    raw_path = database_url.removeprefix("sqlite:///")
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = (Path.cwd() / db_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)


def get_engine() -> Engine:
    global _engine, _engine_url

    if _engine is None or _engine_url != settings.database_url:
        _ensure_database_parent_dir(settings.database_url)
        _engine = create_engine(
            settings.database_url,
            echo=settings.database_echo,
            future=True,
            connect_args=_sqlite_connect_args(settings.database_url),
        )
        _engine_url = settings.database_url

    return _engine


def init_database() -> None:
    metadata.create_all(get_engine())
