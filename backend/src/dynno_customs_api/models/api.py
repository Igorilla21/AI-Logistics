from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dynno_customs_api.models.domain import UserRole


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


class OcrTextLineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_no: int
    text: str
    confidence: float | None = None
    block_no: int | None = None
    paragraph_no: int | None = None
    line_no: int | None = None
    word_count: int = 0
    bounding_box: dict[str, Any] | None = None


class OcrPageResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_no: int
    text: str
    confidence: float | None = None
    image_width: int | None = None
    image_height: int | None = None
    lines: list[OcrTextLineResponse] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


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
    raw_text_ref: str | None = None
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
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


class ValidationResultGroups(BaseModel):
    model_config = ConfigDict(extra="forbid")

    failed: list[ValidationResultResponse] = Field(default_factory=list)
    needs_review: list[ValidationResultResponse] = Field(default_factory=list)
    warnings: list[ValidationResultResponse] = Field(default_factory=list)
    skipped: list[ValidationResultResponse] = Field(default_factory=list)
    passed: list[ValidationResultResponse] = Field(default_factory=list)


class ValidationRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    pack_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    summary: ValidationSummary
    grouped_results: ValidationResultGroups
    report: ValidationReportResponse
    documents: list[NormalizedDocumentResponse]


class ValidationRunSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    pack_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    generated_at: datetime
    summary: ValidationSummary
    document_count: int
    file_names: list[str]


class ValidationRunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ValidationRunSummaryResponse]


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class AuthRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    full_name: str = Field(min_length=2, max_length=255)
    role: UserRole | None = None


class AuthLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class AuthTokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    user: UserResponse


class AuthBootstrapStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    has_users: bool
    registration_open: bool
