from datetime import UTC, datetime
from uuid import uuid4

from dynno_customs_api.models.domain import DocumentFileRecord, DocumentPackRecord
from dynno_customs_api.services.document_pack_store import InMemoryDocumentPackStore


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
