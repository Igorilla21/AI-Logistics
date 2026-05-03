from datetime import UTC, datetime
from uuid import uuid4

from dynno_customs_api.models.domain import (
    DocumentFileRecord,
    DocumentPackRecord,
    OcrDocumentResultRecord,
    OcrPageResultRecord,
)
from dynno_customs_api.services import normalization_service
from dynno_customs_api.services.document_pack_store import InMemoryDocumentPackStore


def test_normalize_document_pack_uses_ocr_raw_text_ref(monkeypatch) -> None:
    store = InMemoryDocumentPackStore()
    now = datetime.now(UTC)
    document_id = uuid4()
    pack = store.save(
        DocumentPackRecord(
            pack_id=uuid4(),
            status="ocr_completed",
            created_at=now,
            updated_at=now,
            files=[
                DocumentFileRecord(
                    document_id=document_id,
                    file_name="invoice.pdf",
                    stored_path="uploads/test/invoice.pdf",
                    content_type="application/pdf",
                    size_bytes=100,
                    uploaded_at=now,
                    sha256="a" * 64,
                )
            ],
            ocr_results=[
                OcrDocumentResultRecord(
                    document_id=document_id,
                    source_file_name="invoice.pdf",
                    source_file_path="uploads/test/invoice.pdf",
                    provider="tesseract",
                    languages="eng+rus",
                    status="completed",
                    pages=[
                        OcrPageResultRecord(page_no=1, text="page 1"),
                        OcrPageResultRecord(page_no=2, text="page 2"),
                    ],
                    raw_text="page 1\n\npage 2",
                    raw_text_ref="storage/ocr/sample/invoice.txt",
                    created_at=now,
                )
            ],
        )
    )
    monkeypatch.setattr(normalization_service, "document_pack_store", store)

    updated_pack = normalization_service.normalize_document_pack(pack.pack_id)

    normalized = updated_pack.normalized_documents[0]
    assert normalized.raw_text_ref == "storage/ocr/sample/invoice.txt"
    assert normalized.pages == 2
    assert normalized.metadata.ocr_provider == "tesseract"
