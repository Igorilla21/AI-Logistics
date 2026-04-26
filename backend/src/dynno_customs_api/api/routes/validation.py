from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter

from dynno_customs_api.models.api import ValidationReportResponse, ValidationSummary


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
