from uuid import uuid4

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
    assert normalized.metadata.classifier == "filename-keyword-v1"
    assert normalized.evidence
