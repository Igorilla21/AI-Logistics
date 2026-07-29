from __future__ import annotations

from uuid import UUID

from dynno_customs_api.models.domain import DocumentPackRecord, NormalizedDocumentRecord
from dynno_customs_api.services.document_pack_store import document_pack_store
from dynno_customs_api.services.normalized_document_builder import build_normalized_document_stub


def normalize_document_pack(pack_id: UUID) -> DocumentPackRecord | None:
    pack = document_pack_store.get(pack_id)
    if pack is None:
        return None

    ocr_results_by_document_id = {
        result.document_id: result
        for result in pack.ocr_results
        if result.status == "completed" and (result.raw_text_ref is not None or result.raw_text or any(page.lines for page in result.pages))
    }

    normalized_documents: list[NormalizedDocumentRecord] = [
        build_normalized_document_stub(
            document_id=file.document_id,
            file_name=file.file_name,
            stored_path=file.stored_path,
            content_type=file.content_type,
            sha256=file.sha256,
            raw_text_ref=ocr_results_by_document_id[file.document_id].raw_text_ref
            if file.document_id in ocr_results_by_document_id
            else None,
            ocr_result=ocr_results_by_document_id[file.document_id] if file.document_id in ocr_results_by_document_id else None,
            pages=len(ocr_results_by_document_id[file.document_id].pages)
            if file.document_id in ocr_results_by_document_id
            else 1,
            ocr_provider=ocr_results_by_document_id[file.document_id].provider
            if file.document_id in ocr_results_by_document_id
            else "stub",
        )
        for file in pack.files
    ]

    updated_pack = pack.model_copy(
        update={
            "status": "extracted",
            "updated_at": max((file.uploaded_at for file in pack.files), default=pack.updated_at),
            "normalized_documents": normalized_documents,
        }
    )
    return document_pack_store.save(updated_pack)


def list_normalized_documents(pack_id: UUID) -> list[NormalizedDocumentRecord] | None:
    pack = document_pack_store.get(pack_id)
    if pack is None:
        return None
    return pack.normalized_documents
