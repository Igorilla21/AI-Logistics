from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BoundingBoxRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class FieldCandidateRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_value: str
    normalized_value: str | float | int | bool | None = None
    confidence: float = Field(ge=0, le=1)
    page_no: int | None = Field(default=None, ge=1)
    text_snippet: str | None = None
    bounding_box: BoundingBoxRecord | None = None


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str
    page_no: int = Field(ge=1)
    field_name: str | None = None
    text_snippet: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    bounding_box: BoundingBoxRecord | None = None


class StringFieldRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str
    raw_value: str | None = None
    normalized_value: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    page_no: int | None = Field(default=None, ge=1)
    text_snippet: str | None = None
    bounding_box: BoundingBoxRecord | None = None
    derived: bool | None = None
    candidates: list[FieldCandidateRecord] | None = None


class DateFieldRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: date
    raw_value: str | None = None
    normalized_value: date | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    page_no: int | None = Field(default=None, ge=1)
    text_snippet: str | None = None
    bounding_box: BoundingBoxRecord | None = None
    derived: bool | None = None
    candidates: list[FieldCandidateRecord] | None = None


class DecimalFieldRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float
    raw_value: str | None = None
    normalized_value: float | None = None
    unit: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    page_no: int | None = Field(default=None, ge=1)
    text_snippet: str | None = None
    bounding_box: BoundingBoxRecord | None = None
    derived: bool | None = None
    candidates: list[FieldCandidateRecord] | None = None


class IntegerFieldRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: int
    raw_value: str | None = None
    normalized_value: int | None = None
    unit: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    page_no: int | None = Field(default=None, ge=1)
    text_snippet: str | None = None
    bounding_box: BoundingBoxRecord | None = None
    derived: bool | None = None
    candidates: list[FieldCandidateRecord] | None = None


class BooleanFieldRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: bool
    raw_value: str | None = None
    normalized_value: bool | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    page_no: int | None = Field(default=None, ge=1)
    text_snippet: str | None = None
    bounding_box: BoundingBoxRecord | None = None
    derived: bool | None = None
    candidates: list[FieldCandidateRecord] | None = None


class LineItemRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line_no: int = Field(ge=1)
    product_name_raw: StringFieldRecord | None = None
    product_name_normalized: StringFieldRecord | None = None
    quantity: DecimalFieldRecord | None = None
    quantity_unit: StringFieldRecord | None = None
    unit_price: DecimalFieldRecord | None = None
    line_total: DecimalFieldRecord | None = None
    batch_no: StringFieldRecord | None = None


class NormalizedDocumentFieldsRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shipper_name: StringFieldRecord | None = None
    buyer_name: StringFieldRecord | None = None
    seller_name: StringFieldRecord | None = None
    consignee_name: StringFieldRecord | None = None
    manufacturer_name: StringFieldRecord | None = None
    contract_no: StringFieldRecord | None = None
    contract_date: DateFieldRecord | None = None
    addendum_no: StringFieldRecord | None = None
    addendum_date: DateFieldRecord | None = None
    invoice_no: StringFieldRecord | None = None
    invoice_date: DateFieldRecord | None = None
    payment_terms: StringFieldRecord | None = None
    incoterms: StringFieldRecord | None = None
    currency: StringFieldRecord | None = None
    container_no: StringFieldRecord | list[StringFieldRecord] | None = None
    gross_weight_kg: DecimalFieldRecord | None = None
    net_weight_kg: DecimalFieldRecord | None = None
    package_weight_kg: DecimalFieldRecord | None = None
    empty_package_weight_kg: DecimalFieldRecord | None = None
    pallet_weight_kg: DecimalFieldRecord | None = None
    pallet_quantity: IntegerFieldRecord | None = None
    items_quantity: IntegerFieldRecord | None = None
    packages_quantity: IntegerFieldRecord | None = None
    package_type: StringFieldRecord | None = None
    bl_no: StringFieldRecord | None = None
    bl_date: DateFieldRecord | None = None
    batch_no: StringFieldRecord | list[StringFieldRecord] | None = None
    manufacture_date: DateFieldRecord | None = None
    expiry_date: DateFieldRecord | None = None
    cargo_description: StringFieldRecord | None = None
    total_amount: DecimalFieldRecord | None = None
    document_presence: BooleanFieldRecord | None = None
    origin_country: StringFieldRecord | None = None


class NormalizedDocumentMetadataRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    role_source: dict[str, str] | None = None
    ocr_provider: str | None = None
    source_hash_sha256: str | None = None
    classifier: str | None = None
    classifier_confidence: float | None = Field(default=None, ge=0, le=1)


class NormalizedDocumentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    document_id: UUID
    document_type: str
    source_file_name: str
    source_file_path: str | None = None
    mime_type: str | None = None
    pages: int = Field(ge=1)
    language: str | None = None
    raw_text_ref: str | None = None
    extraction_status: str
    fields: NormalizedDocumentFieldsRecord = Field(default_factory=NormalizedDocumentFieldsRecord)
    line_items: list[LineItemRecord] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    metadata: NormalizedDocumentMetadataRecord = Field(default_factory=NormalizedDocumentMetadataRecord)


class DocumentFileRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    file_name: str
    stored_path: str
    content_type: str
    size_bytes: int = Field(ge=0)
    uploaded_at: datetime
    sha256: str


OcrStatus = Literal["completed", "failed"]


class OcrPageResultRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_no: int = Field(ge=1)
    text: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    image_width: int | None = Field(default=None, ge=1)
    image_height: int | None = Field(default=None, ge=1)


class OcrDocumentResultRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    source_file_name: str
    source_file_path: str
    provider: str
    languages: str
    status: OcrStatus
    pages: list[OcrPageResultRecord] = Field(default_factory=list)
    raw_text: str = ""
    raw_text_ref: str | None = None
    error_message: str | None = None
    created_at: datetime


class DocumentPackRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    files: list[DocumentFileRecord]
    ocr_results: list[OcrDocumentResultRecord] = Field(default_factory=list)
    normalized_documents: list[NormalizedDocumentRecord] = Field(default_factory=list)


ValidationSeverity = Literal["error", "warning", "info"]
ValidationStatus = Literal["passed", "failed", "skipped", "needs_review"]


class ValidationResultRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_code: str = Field(pattern=r"^R\d{3}$")
    severity: ValidationSeverity
    status: ValidationStatus
    message: str = Field(min_length=1)
    documents: list[str] = Field(min_length=1)
    fields: list[str] = Field(min_length=1)
    observed_values: dict[str, Any] = Field(default_factory=dict)
    expected_values: dict[str, Any] | None = None
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)
    created_at: datetime


class ValidationSummaryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_rules: int
    passed: int
    failed: int
    warnings: int
    needs_review: int
    skipped: int


class ValidationReportRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    report_id: UUID
    pack_id: UUID
    generated_at: datetime
    summary: ValidationSummaryRecord
    results: list[ValidationResultRecord]
