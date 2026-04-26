from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from dynno_customs_api.config import settings
from dynno_customs_api.models.domain import DocumentFileRecord, DocumentPackRecord
from dynno_customs_api.services.document_pack_store import document_pack_store


def _safe_filename(file_name: str) -> str:
    candidate = Path(file_name).name.strip()
    return candidate or "unnamed"


async def create_document_pack(files: list[UploadFile]) -> DocumentPackRecord:
    now = datetime.now(UTC)
    pack_id = uuid4()
    pack_dir = settings.uploads_dir / str(pack_id)
    pack_dir.mkdir(parents=True, exist_ok=True)

    saved_files: list[DocumentFileRecord] = []

    for upload in files:
        content = await upload.read()
        document_id = uuid4()
        safe_name = _safe_filename(upload.filename or "unnamed")
        target_path = pack_dir / safe_name
        target_path.write_bytes(content)

        saved_files.append(
            DocumentFileRecord(
                document_id=document_id,
                file_name=safe_name,
                stored_path=str(target_path.relative_to(settings.uploads_dir.parent)),
                content_type=upload.content_type or "application/octet-stream",
                size_bytes=len(content),
                uploaded_at=now,
                sha256=hashlib.sha256(content).hexdigest(),
            )
        )

    pack = DocumentPackRecord(
        pack_id=pack_id,
        status="uploaded",
        created_at=now,
        updated_at=now,
        files=saved_files,
    )
    return document_pack_store.save(pack)


def get_document_pack(pack_id: UUID) -> DocumentPackRecord | None:
    return document_pack_store.get(pack_id)


def list_document_packs() -> list[DocumentPackRecord]:
    return document_pack_store.list()
