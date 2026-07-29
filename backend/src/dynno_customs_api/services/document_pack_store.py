from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from uuid import UUID

from sqlalchemy import delete, desc, insert, select, update

from dynno_customs_api.models.domain import (
    DocumentFileRecord,
    DocumentPackRecord,
    NormalizedDocumentRecord,
    OcrDocumentResultRecord,
)
from dynno_customs_api.services.database import (
    document_files_table,
    document_packs_table,
    get_engine,
    normalized_documents_table,
    ocr_document_results_table,
)


@dataclass(slots=True)
class InMemoryDocumentPackStore:
    _items: dict[UUID, DocumentPackRecord] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def save(self, pack: DocumentPackRecord) -> DocumentPackRecord:
        with self._lock:
            self._items[pack.pack_id] = pack
        return pack

    def get(self, pack_id: UUID) -> DocumentPackRecord | None:
        with self._lock:
            return self._items.get(pack_id)

    def list(self) -> list[DocumentPackRecord]:
        with self._lock:
            return sorted(self._items.values(), key=lambda item: item.created_at, reverse=True)


class SqlDocumentPackStore:
    def save(self, pack: DocumentPackRecord) -> DocumentPackRecord:
        payload = pack.model_dump(mode="json")
        values = {
            "pack_id": str(pack.pack_id),
            "status": pack.status,
            "created_at": pack.created_at,
            "updated_at": pack.updated_at,
            "payload": payload,
        }

        with get_engine().begin() as connection:
            existing = connection.execute(
                select(document_packs_table.c.pack_id).where(document_packs_table.c.pack_id == str(pack.pack_id))
            ).scalar_one_or_none()

            if existing is None:
                connection.execute(insert(document_packs_table).values(**values))
            else:
                connection.execute(
                    update(document_packs_table)
                    .where(document_packs_table.c.pack_id == str(pack.pack_id))
                    .values(**values)
                )

            connection.execute(delete(document_files_table).where(document_files_table.c.pack_id == str(pack.pack_id)))
            connection.execute(
                delete(ocr_document_results_table).where(ocr_document_results_table.c.pack_id == str(pack.pack_id))
            )
            connection.execute(
                delete(normalized_documents_table).where(normalized_documents_table.c.pack_id == str(pack.pack_id))
            )

            if pack.files:
                connection.execute(
                    insert(document_files_table),
                    [
                        {
                            "document_id": str(item.document_id),
                            "pack_id": str(pack.pack_id),
                            "uploaded_at": item.uploaded_at,
                            "file_name": item.file_name,
                            "stored_path": item.stored_path,
                            "content_type": item.content_type,
                            "size_bytes": item.size_bytes,
                            "sha256": item.sha256,
                            "payload": item.model_dump(mode="json"),
                        }
                        for item in pack.files
                    ],
                )

            if pack.ocr_results:
                connection.execute(
                    insert(ocr_document_results_table),
                    [
                        {
                            "document_id": str(item.document_id),
                            "pack_id": str(pack.pack_id),
                            "created_at": item.created_at,
                            "status": item.status,
                            "source_file_name": item.source_file_name,
                            "payload": item.model_dump(mode="json"),
                        }
                        for item in pack.ocr_results
                    ],
                )

            if pack.normalized_documents:
                connection.execute(
                    insert(normalized_documents_table),
                    [
                        {
                            "document_id": str(item.document_id),
                            "pack_id": str(pack.pack_id),
                            "document_type": item.document_type,
                            "source_file_name": item.source_file_name,
                            "extraction_status": item.extraction_status,
                            "payload": item.model_dump(mode="json"),
                        }
                        for item in pack.normalized_documents
                    ],
                )

        return pack

    def get(self, pack_id: UUID) -> DocumentPackRecord | None:
        with get_engine().begin() as connection:
            row = connection.execute(
                select(document_packs_table.c.payload).where(document_packs_table.c.pack_id == str(pack_id))
            ).one_or_none()
            file_rows = connection.execute(
                select(document_files_table.c.payload)
                .where(document_files_table.c.pack_id == str(pack_id))
                .order_by(document_files_table.c.uploaded_at, document_files_table.c.file_name)
            ).all()
            ocr_rows = connection.execute(
                select(ocr_document_results_table.c.payload)
                .where(ocr_document_results_table.c.pack_id == str(pack_id))
                .order_by(ocr_document_results_table.c.created_at, ocr_document_results_table.c.source_file_name)
            ).all()
            normalized_rows = connection.execute(
                select(normalized_documents_table.c.payload)
                .where(normalized_documents_table.c.pack_id == str(pack_id))
                .order_by(normalized_documents_table.c.source_file_name, normalized_documents_table.c.document_type)
            ).all()

        if row is None:
            return None

        return self._build_pack_from_rows(row.payload, file_rows, ocr_rows, normalized_rows)

    def list(self) -> list[DocumentPackRecord]:
        with get_engine().begin() as connection:
            rows = connection.execute(
                select(document_packs_table.c.pack_id, document_packs_table.c.payload).order_by(desc(document_packs_table.c.created_at))
            ).all()
            file_rows = connection.execute(
                select(document_files_table.c.pack_id, document_files_table.c.payload).order_by(
                    document_files_table.c.pack_id,
                    document_files_table.c.uploaded_at,
                    document_files_table.c.file_name,
                )
            ).all()
            ocr_rows = connection.execute(
                select(ocr_document_results_table.c.pack_id, ocr_document_results_table.c.payload).order_by(
                    ocr_document_results_table.c.pack_id,
                    ocr_document_results_table.c.created_at,
                    ocr_document_results_table.c.source_file_name,
                )
            ).all()
            normalized_rows = connection.execute(
                select(normalized_documents_table.c.pack_id, normalized_documents_table.c.payload).order_by(
                    normalized_documents_table.c.pack_id,
                    normalized_documents_table.c.source_file_name,
                    normalized_documents_table.c.document_type,
                )
            ).all()

        files_by_pack_id: dict[str, list[object]] = defaultdict(list)
        for row in file_rows:
            files_by_pack_id[row.pack_id].append(row)

        ocr_by_pack_id: dict[str, list[object]] = defaultdict(list)
        for row in ocr_rows:
            ocr_by_pack_id[row.pack_id].append(row)

        normalized_by_pack_id: dict[str, list[object]] = defaultdict(list)
        for row in normalized_rows:
            normalized_by_pack_id[row.pack_id].append(row)

        return [
            self._build_pack_from_rows(
                row.payload,
                files_by_pack_id.get(row.pack_id, []),
                ocr_by_pack_id.get(row.pack_id, []),
                normalized_by_pack_id.get(row.pack_id, []),
            )
            for row in rows
        ]

    def clear(self) -> None:
        with get_engine().begin() as connection:
            connection.execute(delete(document_files_table))
            connection.execute(delete(ocr_document_results_table))
            connection.execute(delete(normalized_documents_table))
            connection.execute(delete(document_packs_table))

    @staticmethod
    def _build_pack_from_rows(payload: dict, file_rows: list[object], ocr_rows: list[object], normalized_rows: list[object]) -> DocumentPackRecord:
        files = [DocumentFileRecord.model_validate(row.payload) for row in file_rows]
        ocr_results = [OcrDocumentResultRecord.model_validate(row.payload) for row in ocr_rows]
        normalized_documents = [NormalizedDocumentRecord.model_validate(row.payload) for row in normalized_rows]

        update: dict[str, object] = {}
        if files:
            update["files"] = files
        if ocr_results:
            update["ocr_results"] = ocr_results
        if normalized_documents:
            update["normalized_documents"] = normalized_documents

        base_pack = DocumentPackRecord.model_validate(payload)
        return base_pack.model_copy(update=update)


document_pack_store = SqlDocumentPackStore()
