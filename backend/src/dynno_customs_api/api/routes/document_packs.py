from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from dynno_customs_api.models.api import DocumentPackCreatedResponse, UploadedDocument


router = APIRouter()


@router.post("", response_model=DocumentPackCreatedResponse)
async def create_document_pack(files: list[UploadFile] | None = File(default=None)) -> DocumentPackCreatedResponse:
    received_files = files or []
    uploaded = [
        UploadedDocument(
            file_name=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
        )
        for file in received_files
    ]
    return DocumentPackCreatedResponse(
        pack_id=uuid4(),
        status="uploaded",
        created_at=datetime.now(UTC),
        files=uploaded,
    )
