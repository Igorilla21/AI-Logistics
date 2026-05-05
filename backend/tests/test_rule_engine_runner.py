from datetime import UTC, date, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from dynno_customs_api.main import app
from dynno_customs_api.models.domain import (
    DateFieldRecord,
    DecimalFieldRecord,
    DocumentPackRecord,
    IntegerFieldRecord,
    LineItemRecord,
    NormalizedDocumentFieldsRecord,
    NormalizedDocumentRecord,
    StringFieldRecord,
)
from dynno_customs_api.services.document_pack_store import document_pack_store
from dynno_customs_api.services.rule_engine_runner import run_rule_engine


def _string(value: str, confidence: float = 0.99) -> StringFieldRecord:
    return StringFieldRecord(
        value=value,
        normalized_value=value.lower(),
        confidence=confidence,
        page_no=1,
        text_snippet=value,
    )


def _decimal(value: float, confidence: float = 0.99) -> DecimalFieldRecord:
    return DecimalFieldRecord(value=value, confidence=confidence, page_no=1, text_snippet=str(value))


def _integer(value: int, confidence: float = 0.99) -> IntegerFieldRecord:
    return IntegerFieldRecord(value=value, confidence=confidence, page_no=1, text_snippet=str(value))


def _date(value: date, confidence: float = 0.99) -> DateFieldRecord:
    return DateFieldRecord(value=value, normalized_value=value, confidence=confidence, page_no=1, text_snippet=str(value))


def _document(
    document_type: str,
    fields: NormalizedDocumentFieldsRecord | None = None,
    line_items: list[LineItemRecord] | None = None,
) -> NormalizedDocumentRecord:
    return NormalizedDocumentRecord(
        document_id=uuid4(),
        document_type=document_type,
        source_file_name=f"{document_type}.pdf",
        pages=1,
        extraction_status="completed",
        fields=fields or NormalizedDocumentFieldsRecord(),
        line_items=line_items or [],
        evidence=[],
    )


def _pack(documents: list[NormalizedDocumentRecord]) -> DocumentPackRecord:
    now = datetime.now(UTC)
    return DocumentPackRecord(
        pack_id=uuid4(),
        status="extracted",
        created_at=now,
        updated_at=now,
        files=[],
        normalized_documents=documents,
    )


def _result_by_code(report, rule_code: str):
    return next(result for result in report.results if result.rule_code == rule_code)


def test_rule_engine_runs_catalog_and_detects_mismatches() -> None:
    invoice = _document(
        "invoice",
        NormalizedDocumentFieldsRecord(
            invoice_no=_string("INV-001"),
            total_amount=_decimal(25.0),
        ),
        [
            LineItemRecord(
                line_no=1,
                quantity=_decimal(2.0),
                unit_price=_decimal(10.0),
                line_total=_decimal(25.0),
            )
        ],
    )
    packing_list = _document(
        "packing_list",
        NormalizedDocumentFieldsRecord(
            invoice_no=_string("INV-002"),
            package_type=_string("bags"),
            packages_quantity=_integer(10),
            gross_weight_kg=_decimal(100.0),
            net_weight_kg=_decimal(90.0),
            package_weight_kg=_decimal(10.0),
            container_no=_string("CONT-001"),
        ),
    )

    report = run_rule_engine(_pack([invoice, packing_list]))

    assert report.summary.total_rules == 27
    assert _result_by_code(report, "R007").status == "failed"
    assert _result_by_code(report, "R008").status == "failed"
    assert _result_by_code(report, "R010").status == "passed"
    assert _result_by_code(report, "R012").status == "passed"


def test_rule_engine_checks_coa_and_bl_rules() -> None:
    coa = _document(
        "coa",
        NormalizedDocumentFieldsRecord(
            batch_no=_string("BATCH-001"),
            manufacture_date=_date(date(2026, 1, 10)),
            expiry_date=_date(date(2027, 1, 10)),
        ),
    )
    packing_list = _document(
        "packing_list",
        NormalizedDocumentFieldsRecord(
            packages_quantity=_integer(10),
            gross_weight_kg=_decimal(100.0),
            container_no=_string("CONT-001"),
        ),
    )
    hbl = _document(
        "hbl",
        NormalizedDocumentFieldsRecord(
            bl_date=_date(date(2026, 2, 1)),
            packages_quantity=_integer(10),
            gross_weight_kg=_decimal(100.0),
            container_no=_string("CONT-001"),
            cargo_description=_string("PVC Resin, HS code 3904"),
        ),
    )

    report = run_rule_engine(_pack([coa, packing_list, hbl]))

    assert _result_by_code(report, "R019").status == "passed"
    assert _result_by_code(report, "R022").status == "passed"
    assert _result_by_code(report, "R024").status == "passed"
    assert _result_by_code(report, "R027").status == "failed"


def test_product_matching_excludes_bl_cargo_description() -> None:
    invoice = _document(
        "invoice",
        line_items=[
            LineItemRecord(
                line_no=1,
                product_name_normalized=_string("polyacrylamide stabvisco fnl1"),
            )
        ],
    )
    packing_list = _document(
        "packing_list",
        line_items=[
            LineItemRecord(
                line_no=1,
                product_name_normalized=_string("polyacrylamide stabvisco fnl1"),
            )
        ],
    )
    mbl = _document(
        "mbl",
        NormalizedDocumentFieldsRecord(
            cargo_description=_string("POLYACRYLAMIDE"),
        ),
    )

    report = run_rule_engine(_pack([invoice, packing_list, mbl]))

    assert _result_by_code(report, "R004").status == "passed"


def test_validation_report_endpoint_runs_rule_engine_and_updates_pack_status() -> None:
    pack = document_pack_store.save(
        _pack(
            [
                _document(
                    "invoice",
                    NormalizedDocumentFieldsRecord(invoice_no=_string("INV-001")),
                )
            ]
        )
    )
    client = TestClient(app)

    response = client.post(f"/api/validation/reports/{pack.pack_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["pack_id"] == str(pack.pack_id)
    assert body["summary"]["total_rules"] == 27
    assert document_pack_store.get(pack.pack_id).status in {"failed", "needs_review", "validated"}

    mock_response = client.post("/api/validation/reports/mock")
    assert mock_response.status_code == 200
