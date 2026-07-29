from datetime import UTC, datetime
from uuid import uuid4

from dynno_customs_api.models.domain import (
    ValidationReportRecord,
    ValidationResultRecord,
    ValidationSummaryRecord,
)
from dynno_customs_api.services.validation_report_store import SqlValidationReportStore


def test_sql_validation_report_store_returns_latest_by_pack() -> None:
    store = SqlValidationReportStore()
    pack_id = uuid4()
    first = ValidationReportRecord(
        report_id=uuid4(),
        pack_id=pack_id,
        generated_at=datetime(2026, 5, 1, tzinfo=UTC),
        summary=ValidationSummaryRecord(
            total_rules=1,
            passed=1,
            failed=0,
            warnings=0,
            needs_review=0,
            skipped=0,
        ),
        results=[
            ValidationResultRecord(
                rule_code="R001",
                severity="info",
                status="passed",
                message="ok",
                documents=["invoice"],
                fields=["invoice_no"],
                created_at=datetime(2026, 5, 1, tzinfo=UTC),
            )
        ],
    )
    second = ValidationReportRecord(
        report_id=uuid4(),
        pack_id=pack_id,
        generated_at=datetime(2026, 5, 2, tzinfo=UTC),
        summary=ValidationSummaryRecord(
            total_rules=2,
            passed=2,
            failed=0,
            warnings=0,
            needs_review=0,
            skipped=0,
        ),
        results=[
            ValidationResultRecord(
                rule_code="R002",
                severity="error",
                status="failed",
                message="mismatch",
                documents=["invoice", "packing_list"],
                fields=["gross_weight_kg"],
                created_at=datetime(2026, 5, 2, tzinfo=UTC),
            ),
            ValidationResultRecord(
                rule_code="R003",
                severity="info",
                status="skipped",
                message="not applicable",
                documents=["packing_list"],
                fields=["pallet_quantity"],
                created_at=datetime(2026, 5, 2, tzinfo=UTC),
            ),
        ],
    )

    store.save(first)
    store.save(second)

    latest = store.get_latest(pack_id)

    assert latest == second
    assert [item.rule_code for item in latest.results] == ["R002", "R003"]
