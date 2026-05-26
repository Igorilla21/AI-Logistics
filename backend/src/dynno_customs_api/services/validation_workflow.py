from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import UploadFile

from dynno_customs_api.models.domain import DocumentPackRecord, ValidationReportRecord
from dynno_customs_api.services.document_intake import create_document_pack as create_document_pack_record
from dynno_customs_api.services.document_pack_store import document_pack_store
from dynno_customs_api.services.normalization_service import normalize_document_pack
from dynno_customs_api.services.ocr_service import run_ocr_for_document_pack
from dynno_customs_api.services.rule_engine_runner import derive_pack_status, run_rule_engine
from dynno_customs_api.services.validation_report_store import validation_report_store


@dataclass(slots=True, frozen=True)
class ValidationWorkflowResult:
    pack: DocumentPackRecord
    report: ValidationReportRecord


async def create_validation_run(files: list[UploadFile]) -> ValidationWorkflowResult:
    pack = await create_document_pack_record(files)
    return run_validation_pipeline(pack.pack_id)


def run_validation_pipeline(pack_id: UUID) -> ValidationWorkflowResult | None:
    pack = run_ocr_for_document_pack(pack_id)
    if pack is None:
        return None

    return create_validation_report(pack_id, normalize_if_needed=True)


def create_validation_report(pack_id: UUID, *, normalize_if_needed: bool = True) -> ValidationWorkflowResult | None:
    pack = document_pack_store.get(pack_id)
    if pack is None:
        return None

    if normalize_if_needed and not pack.normalized_documents:
        pack = normalize_document_pack(pack_id)
        if pack is None:
            return None

    report = run_rule_engine(pack)
    updated_pack = pack.model_copy(
        update={
            "status": derive_pack_status(report),
            "updated_at": report.generated_at,
        }
    )
    document_pack_store.save(updated_pack)
    validation_report_store.save(report)
    return ValidationWorkflowResult(pack=updated_pack, report=report)


def get_latest_validation_run(pack_id: UUID) -> ValidationWorkflowResult | None:
    pack = document_pack_store.get(pack_id)
    if pack is None:
        return None

    report = validation_report_store.get_latest(pack_id)
    if report is None:
        return None

    return ValidationWorkflowResult(pack=pack, report=report)


def list_validation_runs() -> list[ValidationWorkflowResult]:
    items: list[ValidationWorkflowResult] = []
    for pack in document_pack_store.list():
        report = validation_report_store.get_latest(pack.pack_id)
        if report is not None:
            items.append(ValidationWorkflowResult(pack=pack, report=report))

    items.sort(key=lambda item: item.report.generated_at, reverse=True)
    return items
