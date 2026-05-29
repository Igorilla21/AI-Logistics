from uuid import uuid4

from dynno_customs_api.config import ROOT_DIR, settings
from dynno_customs_api.services.normalized_document_builder import build_normalized_document_stub


def test_build_stub_normalized_document() -> None:
    normalized = build_normalized_document_stub(
        document_id=uuid4(),
        file_name="commercial_invoice_001.pdf",
        stored_path="uploads/sample/commercial_invoice_001.pdf",
        content_type="application/pdf",
        sha256="a" * 64,
    )

    assert normalized.document_type == "invoice"
    assert normalized.extraction_status == "partial"
    assert normalized.metadata.classifier == "filename-keyword-v2"
    assert normalized.evidence


def test_build_stub_uses_ocr_text_for_classification_when_filename_is_generic() -> None:
    raw_text_dir = settings.temp_dir / "tests" / "normalized-builder"
    raw_text_dir.mkdir(parents=True, exist_ok=True)
    raw_text_path = raw_text_dir / "packing-list.txt"
    raw_text_path.write_text(
        "PACKING LIST SOYUZOPTHIM LTD INV.NO.: 26RT0004",
        encoding="utf-8",
    )

    normalized = build_normalized_document_stub(
        document_id=uuid4(),
        file_name="scan_001.pdf",
        stored_path="uploads/sample/scan_001.pdf",
        content_type="application/pdf",
        sha256="b" * 64,
        raw_text_ref=str(raw_text_path.relative_to(ROOT_DIR)),
        ocr_provider="tesseract",
    )

    assert normalized.document_type == "packing_list"
    assert normalized.metadata.classifier == "ocr-text-keyword-v1"


def test_build_normalized_document_extracts_fields_from_raw_text_ref() -> None:
    raw_text_dir = settings.temp_dir / "tests" / "normalized-builder"
    raw_text_dir.mkdir(parents=True, exist_ok=True)
    raw_text_path = raw_text_dir / "invoice.txt"
    raw_text_path.write_text(
        "QINGDAO RAITTE TECHNOLOGIES CO.,LTD. COMMERCIAL INVOICE "
        "TO:000 SOYUZOPTHIM LTD DATE: APR.13,2026 INV.NO.: 26RT0004 "
        "ADD 68 // Contract Ne QRT-SOH dated 01.09.2025 "
        "POLYACRYLAMIDE StabVisco FNL1 18000.00KG CNY9.1000/MT CNY 163800.00 "
        "PACKING: IN NET 25KG BAG CNY 163800.00 For",
        encoding="utf-8",
    )

    normalized = build_normalized_document_stub(
        document_id=uuid4(),
        file_name="commercial_invoice_001.pdf",
        stored_path="uploads/sample/commercial_invoice_001.pdf",
        content_type="application/pdf",
        sha256="a" * 64,
        raw_text_ref=str(raw_text_path.relative_to(ROOT_DIR)),
        ocr_provider="tesseract",
    )

    assert normalized.fields.invoice_no.value == "26RT0004"
    assert normalized.fields.contract_no.value == "QRT-SOH"
    assert normalized.fields.addendum_no.value == "ADD 68"
    assert normalized.metadata.ocr_provider == "tesseract"
    assert normalized.line_items[0].unit_price.value == 9100.0
