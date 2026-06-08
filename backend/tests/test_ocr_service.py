from datetime import UTC, datetime
import shutil
from uuid import uuid4

from dynno_customs_api.config import settings
from dynno_customs_api.models.domain import DocumentFileRecord, DocumentPackRecord, OcrDocumentResultRecord
from dynno_customs_api.services.document_pack_store import InMemoryDocumentPackStore
from dynno_customs_api.services import ocr_service


class StubOcrProvider:
    name = "stub"

    def process_document(self, document: DocumentFileRecord) -> OcrDocumentResultRecord:
        now = datetime.now(UTC)
        return OcrDocumentResultRecord(
            document_id=document.document_id,
            source_file_name=document.file_name,
            source_file_path=document.stored_path,
            provider=self.name,
            languages="eng",
            status="completed",
            raw_text=f"stub text for {document.file_name}",
            provider_metadata={"provider": self.name},
            created_at=now,
        )


def test_run_ocr_for_document_pack_uses_configured_provider(monkeypatch) -> None:
    store = InMemoryDocumentPackStore()
    now = datetime.now(UTC)
    document_id = uuid4()
    output_dir = settings.temp_dir / "tests" / "ocr-service-provider"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
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
                sha256="a" * 64,
            )
        ],
    )
    store.save(pack)

    monkeypatch.setattr(ocr_service, "document_pack_store", store)
    monkeypatch.setattr(ocr_service.settings, "ocr_provider", "stub")
    monkeypatch.setattr(ocr_service.settings, "ocr_output_dir", output_dir)
    monkeypatch.setattr(
        ocr_service,
        "ocr_provider_registry",
        ocr_service.OcrProviderRegistry({"stub": StubOcrProvider()}),
    )

    updated_pack = ocr_service.run_ocr_for_document_pack(pack.pack_id)

    assert updated_pack is not None
    assert updated_pack.status == "ocr_completed"
    assert updated_pack.ocr_results[0].provider == "stub"
    assert updated_pack.ocr_results[0].provider_metadata["provider"] == "stub"
    assert updated_pack.ocr_results[0].raw_text_ref is not None
