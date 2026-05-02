from datetime import UTC, datetime
from uuid import uuid4

from dynno_customs_api.models.domain import DocumentFileRecord, DocumentPackRecord, OcrDocumentResultRecord, OcrPageResultRecord
from dynno_customs_api.services.document_pack_store import InMemoryDocumentPackStore
from dynno_customs_api.services import ocr_service


def _document(file_name: str = "invoice.png") -> DocumentFileRecord:
    return DocumentFileRecord(
        document_id=uuid4(),
        file_name=file_name,
        stored_path=f"uploads/test/{file_name}",
        content_type="image/png",
        size_bytes=100,
        uploaded_at=datetime.now(UTC),
        sha256="a" * 64,
    )


def test_run_ocr_for_document_pack_updates_pack_with_results(monkeypatch) -> None:
    store = InMemoryDocumentPackStore()
    document = _document()
    now = datetime.now(UTC)
    pack = store.save(
        DocumentPackRecord(
            pack_id=uuid4(),
            status="uploaded",
            created_at=now,
            updated_at=now,
            files=[document],
        )
    )

    def fake_run_tesseract_ocr(file_record):
        assert file_record == document
        return OcrDocumentResultRecord(
            document_id=file_record.document_id,
            source_file_name=file_record.file_name,
            source_file_path=file_record.stored_path,
            provider="tesseract",
            languages="eng+rus",
            status="completed",
            pages=[OcrPageResultRecord(page_no=1, text="Invoice INV-001", confidence=0.91)],
            raw_text="Invoice INV-001",
            created_at=datetime.now(UTC),
        )

    monkeypatch.setattr(ocr_service, "document_pack_store", store)
    monkeypatch.setattr(ocr_service, "run_tesseract_ocr", fake_run_tesseract_ocr)

    updated_pack = ocr_service.run_ocr_for_document_pack(pack.pack_id)

    assert updated_pack.status == "ocr_completed"
    assert updated_pack.ocr_results[0].raw_text == "Invoice INV-001"
    assert store.get(pack.pack_id).ocr_results == updated_pack.ocr_results


def test_list_ocr_results_returns_none_for_missing_pack(monkeypatch) -> None:
    monkeypatch.setattr(ocr_service, "document_pack_store", InMemoryDocumentPackStore())

    assert ocr_service.list_ocr_results(uuid4()) is None
