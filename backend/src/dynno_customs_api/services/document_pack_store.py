from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from uuid import UUID

from dynno_customs_api.models.domain import DocumentPackRecord


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


document_pack_store = InMemoryDocumentPackStore()
