from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UploadedDocument(BaseModel):
    file_name: str
    content_type: str


class DocumentPackCreatedResponse(BaseModel):
    pack_id: UUID
    status: str
    created_at: datetime
    files: list[UploadedDocument]


class ValidationSummary(BaseModel):
    total_rules: int
    passed: int
    failed: int
    warnings: int
    needs_review: int
    skipped: int


class ValidationReportResponse(BaseModel):
    schema_version: str
    report_id: UUID
    pack_id: UUID
    generated_at: datetime
    summary: ValidationSummary
    results: list[dict]
