from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile

from dynno_customs_api.models.api import (
    DocumentPackCreatedResponse,
    DocumentPackListResponse,
    UploadedDocument,
)
from dynno_customs_api.models.domain import DocumentPackRecord
from dynno_customs_api.services.document_intake import (
    create_document_pack as create_document_pack_record,
    get_document_pack,
    list_document_packs,
)


router = APIRouter()


def _to_response(pack: DocumentPackRecord) -> DocumentPackCreatedResponse:
    return DocumentPackCreatedResponse(
        pack_id=pack.pack_id,
        status=pack.status,
        created_at=pack.created_at,
        updated_at=pack.updated_at,
        files=[
            UploadedDocument(
                document_id=file.document_id,
                file_name=file.file_name,
                content_type=file.content_type,
                size_bytes=file.size_bytes,
                sha256=file.sha256,
                stored_path=file.stored_path,
                uploaded_at=file.uploaded_at,
            )
            for file in pack.files
        ],
    )


@router.post("", response_model=DocumentPackCreatedResponse)
async def create_document_pack(files: list[UploadFile] | None = File(default=None)) -> DocumentPackCreatedResponse:
    pack = await create_document_pack_record(files or [])
    return _to_response(pack)


@router.get("", response_model=DocumentPackListResponse)
async def get_document_pack_list() -> DocumentPackListResponse:
    return DocumentPackListResponse(items=[_to_response(pack) for pack in list_document_packs()])


@router.get("/{pack_id}", response_model=DocumentPackCreatedResponse)
async def get_document_pack_by_id(pack_id: UUID) -> DocumentPackCreatedResponse:
    pack = get_document_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")
    return _to_response(pack)
