from datetime import UTC, datetime
from uuid import uuid4

from dynno_customs_api.models.domain import (
    DocumentFileRecord,
    DocumentPackRecord,
    NormalizedDocumentFieldsRecord,
    NormalizedDocumentMetadataRecord,
    NormalizedDocumentRecord,
    OcrDocumentResultRecord,
    OcrPageResultRecord,
)
from dynno_customs_api.services.document_pack_store import InMemoryDocumentPackStore, SqlDocumentPackStore


def test_store_roundtrip() -> None:
    store = InMemoryDocumentPackStore()
    now = datetime.now(UTC)
    pack = DocumentPackRecord(
        pack_id=uuid4(),
        status="uploaded",
        created_at=now,
        updated_at=now,
        files=[
            DocumentFileRecord(
                document_id=uuid4(),
                file_name="invoice.pdf",
                stored_path="uploads/test/invoice.pdf",
                content_type="application/pdf",
                size_bytes=123,
                uploaded_at=now,
                sha256="a" * 64,
            )
        ],
    )

    saved = store.save(pack)

    assert store.get(pack.pack_id) == saved
    assert len(store.list()) == 1


def test_sql_store_roundtrip() -> None:
    store = SqlDocumentPackStore()
    now = datetime.now(UTC)
    document_id = uuid4()
    pack = DocumentPackRecord(
        pack_id=uuid4(),
        status="uploaded",
        created_at=now,
        updated_at=now,
        files=[
            DocumentFileRecord(
                document_id=document_id,
                file_name="invoice.pdf",
                stored_path="uploads/test/invoice.pdf",
                content_type="application/pdf",
                size_bytes=123,
                uploaded_at=now,
                sha256="b" * 64,
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
                    OcrPageResultRecord(
                        page_no=1,
                        text="invoice text",
                        confidence=0.97,
                        image_width=100,
                        image_height=50,
                    )
                ],
                raw_text="invoice text",
                raw_text_ref="storage/ocr/test/invoice.txt",
                created_at=now,
            )
        ],
        normalized_documents=[
            NormalizedDocumentRecord(
                document_id=document_id,
                document_type="invoice",
                source_file_name="invoice.pdf",
                source_file_path="uploads/test/invoice.pdf",
                mime_type="application/pdf",
                pages=1,
                language="eng",
                raw_text_ref="storage/ocr/test/invoice.txt",
                extraction_status="partial",
                fields=NormalizedDocumentFieldsRecord(),
                line_items=[],
                evidence=[],
                metadata=NormalizedDocumentMetadataRecord(ocr_provider="tesseract"),
            )
        ],
    )

    saved = store.save(pack)

    assert store.get(pack.pack_id) == saved
    assert len(store.list()) == 1
