from dynno_customs_api.services.document_classifier import classify_document


def test_classify_invoice_from_filename() -> None:
    result = classify_document("commercial_invoice_001.pdf", "application/pdf")

    assert result.document_type == "invoice"
    assert result.confidence >= 0.9


def test_classify_hbl_from_filename() -> None:
    result = classify_document("shipment_hbl_scan.pdf", "application/pdf")

    assert result.document_type == "hbl"
