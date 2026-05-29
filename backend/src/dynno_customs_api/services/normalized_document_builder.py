from __future__ import annotations

from dynno_customs_api.models.domain import (
    EvidenceRecord,
    NormalizedDocumentFieldsRecord,
    NormalizedDocumentMetadataRecord,
    NormalizedDocumentRecord,
    StringFieldRecord,
)
from dynno_customs_api.services.document_classifier import classify_document
from dynno_customs_api.services.text_extractor import extract_fields, read_raw_text


def build_normalized_document_stub(
    *,
    document_id,
    file_name: str,
    stored_path: str,
    content_type: str,
    sha256: str,
    raw_text_ref: str | None = None,
    pages: int = 1,
    ocr_provider: str = "stub",
) -> NormalizedDocumentRecord:
    raw_text = read_raw_text(raw_text_ref)
    classified = classify_document(file_name, content_type, raw_text)
    fields, line_items = extract_fields(classified.document_type, raw_text)
    evidence = [
        EvidenceRecord(
            document_type=classified.document_type,
            page_no=1,
            field_name="document_type",
            text_snippet=f"Classified from filename: {file_name}",
            confidence=classified.confidence,
        )
    ]

    # Keep the fallback conservative: only add fields we can infer from the filename.
    lowered_name = file_name.lower()
    if "prepayment" in lowered_name or "payment" in lowered_name or "mt103" in lowered_name:
        fields.document_presence = None

    if classified.document_type in {"invoice", "packing_list"} and fields.invoice_no is None:
        fields.invoice_no = StringFieldRecord(
            value=file_name,
            raw_value=file_name,
            normalized_value=file_name.lower(),
            confidence=0.15,
            page_no=1,
            text_snippet="Stub value derived from filename only.",
            derived=True,
        )

    return NormalizedDocumentRecord(
        document_id=document_id,
        document_type=classified.document_type,
        source_file_name=file_name,
        source_file_path=stored_path,
        mime_type=content_type,
        pages=pages,
        language="unknown",
        raw_text_ref=raw_text_ref,
        extraction_status="partial",
        fields=fields,
        line_items=line_items,
        evidence=evidence,
        metadata=NormalizedDocumentMetadataRecord(
            ocr_provider=ocr_provider,
            source_hash_sha256=sha256,
            classifier=classified.classifier,
            classifier_confidence=classified.confidence,
        ),
    )
