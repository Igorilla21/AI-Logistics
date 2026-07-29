from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from dynno_customs_api.models.domain import DocumentFileRecord, OcrDocumentResultRecord


class OcrProvider(Protocol):
    name: str

    def process_document(self, document: DocumentFileRecord) -> OcrDocumentResultRecord: ...


class OcrProviderRegistry:
    def __init__(self, providers: Mapping[str, OcrProvider]) -> None:
        self._providers = {name.lower(): provider for name, provider in providers.items()}

    def get(self, name: str) -> OcrProvider:
        provider = self._providers.get(name.lower())
        if provider is None:
            available = ", ".join(sorted(self._providers))
            raise ValueError(f"Unknown OCR provider '{name}'. Available providers: {available}")
        return provider
