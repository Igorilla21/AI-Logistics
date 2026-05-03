from __future__ import annotations

from uuid import UUID

from dynno_customs_api.config import ROOT_DIR, settings
from dynno_customs_api.models.domain import DocumentPackRecord, OcrDocumentResultRecord
from dynno_customs_api.services.document_pack_store import document_pack_store
from dynno_customs_api.services.tesseract_ocr import run_tesseract_ocr


def run_ocr_for_document_pack(pack_id: UUID) -> DocumentPackRecord | None:
    pack = document_pack_store.get(pack_id)
    if pack is None:
        return None

    results = [_persist_raw_text(pack_id, run_tesseract_ocr(document)) for document in pack.files]
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


def _persist_raw_text(pack_id: UUID, result: OcrDocumentResultRecord) -> OcrDocumentResultRecord:
    if result.status != "completed":
        return result

    output_dir = settings.ocr_output_dir / str(pack_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{result.document_id}.txt"
    output_path.write_text(result.raw_text, encoding="utf-8")

    return result.model_copy(
        update={
            "raw_text_ref": str(output_path.relative_to(ROOT_DIR)),
        }
    )
