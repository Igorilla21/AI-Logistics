from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UploadedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID | None = None
    file_name: str
    content_type: str
    size_bytes: int | None = None
    sha256: str | None = None
    stored_path: str | None = None
    uploaded_at: datetime | None = None


class DocumentPackCreatedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    files: list[UploadedDocument]


class DocumentPackListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DocumentPackCreatedResponse]


class ValidationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_rules: int
    passed: int
    failed: int
    warnings: int
    needs_review: int
    skipped: int


class ValidationReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    report_id: UUID
    pack_id: UUID
    generated_at: datetime
    summary: ValidationSummary
    results: list[dict]
