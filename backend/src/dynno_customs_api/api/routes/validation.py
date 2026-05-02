from datetime import UTC, datetime
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from dynno_customs_api.models.api import (
    EvidenceResponse,
    ValidationReportResponse,
    ValidationResultResponse,
    ValidationSummary,
)
from dynno_customs_api.models.domain import ValidationReportRecord
from dynno_customs_api.services.document_intake import get_document_pack
from dynno_customs_api.services.document_pack_store import document_pack_store
from dynno_customs_api.services.normalization_service import normalize_document_pack
from dynno_customs_api.services.rule_engine_runner import derive_pack_status, run_rule_engine


router = APIRouter()


def _to_response(report: ValidationReportRecord) -> ValidationReportResponse:
    return ValidationReportResponse(
        schema_version=report.schema_version,
        report_id=report.report_id,
        pack_id=report.pack_id,
        generated_at=report.generated_at,
        summary=ValidationSummary(**report.summary.model_dump()),
        results=[
            ValidationResultResponse(
                rule_code=result.rule_code,
                severity=result.severity,
                status=result.status,
                message=result.message,
                documents=result.documents,
                fields=result.fields,
                observed_values=result.observed_values,
                expected_values=result.expected_values,
                evidence=[
                    EvidenceResponse(
                        document_type=item.document_type,
                        page_no=item.page_no,
                        field_name=item.field_name,
                        text_snippet=item.text_snippet,
                        confidence=item.confidence,
                    )
                    for item in result.evidence
                ],
                confidence=result.confidence,
                created_at=result.created_at,
            )
            for result in report.results
        ],
    )


@router.post("/reports/mock", response_model=ValidationReportResponse)
async def create_mock_validation_report() -> ValidationReportResponse:
    return ValidationReportResponse(
        schema_version="1.0.0",
        report_id=uuid4(),
        pack_id=uuid4(),
        generated_at=datetime.now(UTC),
        summary=ValidationSummary(
            total_rules=0,
            passed=0,
            failed=0,
            warnings=0,
            needs_review=0,
            skipped=0,
        ),
        results=[],
    )


@router.post("/reports/{pack_id}", response_model=ValidationReportResponse)
async def create_validation_report(pack_id: UUID) -> ValidationReportResponse:
    pack = get_document_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")

    if not pack.normalized_documents:
        pack = normalize_document_pack(pack_id)
        if pack is None:
            raise HTTPException(status_code=404, detail="Document pack not found.")

    report = run_rule_engine(pack)
    updated_pack = pack.model_copy(
        update={
            "status": derive_pack_status(report),
            "updated_at": report.generated_at,
        }
    )
    document_pack_store.save(updated_pack)
    return _to_response(report)
