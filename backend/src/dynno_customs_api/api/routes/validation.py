from datetime import UTC, datetime
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from dynno_customs_api.models.api import (
    ValidationReportResponse,
)
from dynno_customs_api.api.serializers import to_validation_report_response
from dynno_customs_api.models.api import ValidationSummary
from dynno_customs_api.services.validation_workflow import create_validation_report as create_validation_report_workflow


router = APIRouter()


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
    result = create_validation_report_workflow(pack_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")

    return to_validation_report_response(result.report)
