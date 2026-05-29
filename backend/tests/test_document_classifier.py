from dynno_customs_api.services.document_classifier import classify_document


def test_classify_invoice_from_filename() -> None:
    result = classify_document("commercial_invoice_001.pdf", "application/pdf")

    assert result.document_type == "invoice"
    assert result.confidence >= 0.9


def test_classify_hbl_from_filename() -> None:
    result = classify_document("shipment_hbl_scan.pdf", "application/pdf")

    assert result.document_type == "hbl"


def test_classify_common_shortcuts_from_filename() -> None:
    assert classify_document("CI -05.pdf", "application/pdf").document_type == "invoice"
    assert classify_document("PL-05.pdf", "application/pdf").document_type == "packing_list"
    assert classify_document("Add 05 signed.pdf", "application/pdf").document_type == "addendum"
    assert classify_document("Seawaybill.pdf", "application/pdf").document_type == "mbl"
    assert classify_document("Bank slip.pdf", "application/pdf").document_type == "payment_confirmation"
    assert classify_document("CO Copy.pdf", "application/pdf").document_type == "certificate_of_origin"


def test_classify_from_ocr_text_when_filename_is_weak() -> None:
    result = classify_document(
        "scan_001.pdf",
        "application/pdf",
        "QINGDAO RAITTE TECHNOLOGIES CO., LTD COMMERCIAL INVOICE INV.NO.: 26RT0004",
    )

    assert result.document_type == "invoice"
    assert result.classifier == "ocr-text-keyword-v1"
