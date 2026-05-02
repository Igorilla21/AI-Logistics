from __future__ import annotations

from uuid import UUID

from dynno_customs_api.models.domain import DocumentPackRecord, OcrDocumentResultRecord
from dynno_customs_api.services.document_pack_store import document_pack_store
from dynno_customs_api.services.tesseract_ocr import run_tesseract_ocr


def run_ocr_for_document_pack(pack_id: UUID) -> DocumentPackRecord | None:
    pack = document_pack_store.get(pack_id)
    if pack is None:
        return None

    results = [run_tesseract_ocr(document) for document in pack.files]
    status = "ocr_failed" if any(result.status == "failed" for result in results) else "ocr_completed"
    updated_at = max((result.created_at for result in results), default=pack.updated_at)

    updated_pack = pack.model_copy(
        update={
            "status": status,
            "updated_at": updated_at,
            "ocr_results": results,
        }
    )
    return document_pack_store.save(updated_pack)


def list_ocr_results(pack_id: UUID) -> list[OcrDocumentResultRecord] | None:
    pack = document_pack_store.get(pack_id)
    if pack is None:
        return None
    return pack.ocr_results
