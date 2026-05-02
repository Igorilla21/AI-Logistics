from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class FieldValueResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    value: str | float | int | bool
    raw_value: str | None = None
    normalized_value: str | float | int | bool | None = None
    confidence: float | None = None
    page_no: int | None = None
    text_snippet: str | None = None
    derived: bool | None = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str
    page_no: int
    field_name: str | None = None
    text_snippet: str
    confidence: float | None = None


class NormalizedDocumentResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: str
    document_id: UUID
    document_type: str
    source_file_name: str
    source_file_path: str | None = None
    mime_type: str | None = None
    pages: int
    language: str | None = None
    raw_text_ref: str | None = None
    extraction_status: str
    fields: dict
    line_items: list[dict]
    evidence: list[EvidenceResponse]
    metadata: dict


class NormalizedDocumentListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: UUID
    items: list[NormalizedDocumentResponse]


class OcrPageResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_no: int
    text: str
    confidence: float | None = None
    image_width: int | None = None
    image_height: int | None = None


class OcrDocumentResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    source_file_name: str
    source_file_path: str
    provider: str
    languages: str
    status: str
    pages: list[OcrPageResultResponse]
    raw_text: str
    error_message: str | None = None
    created_at: datetime


class OcrDocumentListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: UUID
    items: list[OcrDocumentResultResponse]


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


class ValidationResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_code: str = Field(pattern=r"^R\d{3}$")
    severity: str
    status: str
    message: str
    documents: list[str]
    fields: list[str]
    observed_values: dict[str, Any]
    expected_values: dict[str, Any] | None = None
    evidence: list[EvidenceResponse]
    confidence: float | None = None
    created_at: datetime


class ValidationReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    report_id: UUID
    pack_id: UUID
    generated_at: datetime
    summary: ValidationSummary
    results: list[ValidationResultResponse]
