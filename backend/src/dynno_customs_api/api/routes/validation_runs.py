from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile

from dynno_customs_api.api.dependencies import CurrentAuthSession
from dynno_customs_api.api.serializers import (
    to_validation_run_response,
    to_validation_run_summary_response,
)
from dynno_customs_api.models.api import ValidationRunListResponse, ValidationRunResponse, ValidationRunSummaryResponse
from dynno_customs_api.services.validation_workflow import (
    create_validation_run as create_validation_run_workflow,
    get_latest_validation_run as get_latest_validation_run_workflow,
    list_validation_runs as list_validation_run_workflows,
)


router = APIRouter()


@router.post("", response_model=ValidationRunResponse)
async def create_validation_run(
    _auth_session: CurrentAuthSession,
    files: list[UploadFile] | None = File(default=None),
) -> ValidationRunResponse:
    result = await create_validation_run_workflow(files or [])
    return to_validation_run_response(result)


@router.get("", response_model=ValidationRunListResponse)
async def list_validation_runs(_auth_session: CurrentAuthSession) -> ValidationRunListResponse:
    items: list[ValidationRunSummaryResponse] = [
        to_validation_run_summary_response(item) for item in list_validation_run_workflows()
    ]
    return ValidationRunListResponse(items=items)


@router.get("/{pack_id}", response_model=ValidationRunResponse)
async def get_latest_validation_run(pack_id: UUID, _auth_session: CurrentAuthSession) -> ValidationRunResponse:
    result = get_latest_validation_run_workflow(pack_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")

    return to_validation_run_response(result)
