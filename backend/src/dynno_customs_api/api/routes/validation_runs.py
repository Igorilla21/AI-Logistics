from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile

from dynno_customs_api.api.serializers import (
    group_validation_results,
    to_normalized_document_response,
    to_validation_report_response,
)
from dynno_customs_api.models.api import ValidationRunResponse
from dynno_customs_api.models.domain import DocumentPackRecord, ValidationReportRecord
from dynno_customs_api.services.document_intake import create_document_pack as create_document_pack_record
from dynno_customs_api.services.document_pack_store import document_pack_store
from dynno_customs_api.services.normalization_service import normalize_document_pack
from dynno_customs_api.services.ocr_service import run_ocr_for_document_pack
from dynno_customs_api.services.rule_engine_runner import derive_pack_status, run_rule_engine
from dynno_customs_api.services.validation_report_store import validation_report_store


router = APIRouter()


def _to_run_response(pack: DocumentPackRecord, report: ValidationReportRecord) -> ValidationRunResponse:
    report_response = to_validation_report_response(report)
    return ValidationRunResponse(
        run_id=report.report_id,
        pack_id=pack.pack_id,
        status=pack.status,
        created_at=pack.created_at,
        updated_at=pack.updated_at,
        summary=report_response.summary,
        grouped_results=group_validation_results(report),
        report=report_response,
        documents=[to_normalized_document_response(item) for item in pack.normalized_documents],
    )


@router.post("", response_model=ValidationRunResponse)
async def create_validation_run(files: list[UploadFile] | None = File(default=None)) -> ValidationRunResponse:
    pack = await create_document_pack_record(files or [])

    pack = run_ocr_for_document_pack(pack.pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")

    pack = normalize_document_pack(pack.pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")

    report = run_rule_engine(pack)
    updated_pack = pack.model_copy(
        update={
            "status": derive_pack_status(report),
            "updated_at": report.generated_at,
        }
    )
    document_pack_store.save(updated_pack)
    validation_report_store.save(report)
    return _to_run_response(updated_pack, report)


@router.get("/{pack_id}", response_model=ValidationRunResponse)
async def get_latest_validation_run(pack_id: UUID) -> ValidationRunResponse:
    pack = document_pack_store.get(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")

    report = validation_report_store.get_latest(pack_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Validation report not found.")

    return _to_run_response(pack, report)
