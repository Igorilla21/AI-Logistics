from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile

from dynno_customs_api.api.dependencies import CurrentAuthSession
from dynno_customs_api.models.api import (
    DocumentPackCreatedResponse,
    DocumentPackListResponse,
    NormalizedDocumentListResponse,
    NormalizedDocumentResponse,
    OcrDocumentListResponse,
    OcrDocumentResultResponse,
    OcrPageResultResponse,
    OcrTextLineResponse,
    UploadedDocument,
)
from dynno_customs_api.models.domain import DocumentPackRecord, NormalizedDocumentRecord, OcrDocumentResultRecord
from dynno_customs_api.services.document_intake import (
    create_document_pack as create_document_pack_record,
    get_document_pack,
    list_document_packs,
)
from dynno_customs_api.services.normalization_service import (
    list_normalized_documents,
    normalize_document_pack,
)
from dynno_customs_api.services.ocr_service import list_ocr_results, run_ocr_for_document_pack


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


def _to_normalized_response(document: NormalizedDocumentRecord) -> NormalizedDocumentResponse:
    return NormalizedDocumentResponse(
        schema_version=document.schema_version,
        document_id=document.document_id,
        document_type=document.document_type,
        source_file_name=document.source_file_name,
        source_file_path=document.source_file_path,
        mime_type=document.mime_type,
        pages=document.pages,
        language=document.language,
        raw_text_ref=document.raw_text_ref,
        extraction_status=document.extraction_status,
        fields=document.fields.model_dump(exclude_none=True),
        line_items=[item.model_dump(exclude_none=True) for item in document.line_items],
        evidence=[
            {
                "document_type": item.document_type,
                "page_no": item.page_no,
                "field_name": item.field_name,
                "text_snippet": item.text_snippet,
                "confidence": item.confidence,
            }
            for item in document.evidence
        ],
        metadata=document.metadata.model_dump(exclude_none=True),
    )


def _to_ocr_response(result: OcrDocumentResultRecord) -> OcrDocumentResultResponse:
    return OcrDocumentResultResponse(
        document_id=result.document_id,
        source_file_name=result.source_file_name,
        source_file_path=result.source_file_path,
        provider=result.provider,
        languages=result.languages,
        status=result.status,
        pages=[
            OcrPageResultResponse(
                page_no=page.page_no,
                text=page.text,
                confidence=page.confidence,
                image_width=page.image_width,
                image_height=page.image_height,
                lines=[
                    OcrTextLineResponse(
                        page_no=line.page_no,
                        text=line.text,
                        confidence=line.confidence,
                        block_no=line.block_no,
                        paragraph_no=line.paragraph_no,
                        line_no=line.line_no,
                        word_count=line.word_count,
                        bounding_box=line.bounding_box.model_dump(mode="json") if line.bounding_box else None,
                    )
                    for line in page.lines
                ],
                provider_metadata=page.provider_metadata,
            )
            for page in result.pages
        ],
        raw_text=result.raw_text,
        raw_text_ref=result.raw_text_ref,
        provider_metadata=result.provider_metadata,
        error_message=result.error_message,
        created_at=result.created_at,
    )


@router.post("", response_model=DocumentPackCreatedResponse)
async def create_document_pack(
    _auth_session: CurrentAuthSession,
    files: list[UploadFile] | None = File(default=None),
) -> DocumentPackCreatedResponse:
    pack = await create_document_pack_record(files or [])
    return _to_response(pack)


@router.get("", response_model=DocumentPackListResponse)
async def get_document_pack_list(_auth_session: CurrentAuthSession) -> DocumentPackListResponse:
    return DocumentPackListResponse(items=[_to_response(pack) for pack in list_document_packs()])


@router.get("/{pack_id}", response_model=DocumentPackCreatedResponse)
async def get_document_pack_by_id(pack_id: UUID, _auth_session: CurrentAuthSession) -> DocumentPackCreatedResponse:
    pack = get_document_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")
    return _to_response(pack)


@router.post("/{pack_id}/ocr", response_model=OcrDocumentListResponse)
async def run_ocr_for_pack(pack_id: UUID, _auth_session: CurrentAuthSession) -> OcrDocumentListResponse:
    pack = run_ocr_for_document_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")
    return OcrDocumentListResponse(
        pack_id=pack_id,
        items=[_to_ocr_response(item) for item in pack.ocr_results],
    )


@router.get("/{pack_id}/ocr-results", response_model=OcrDocumentListResponse)
async def get_ocr_results(pack_id: UUID, _auth_session: CurrentAuthSession) -> OcrDocumentListResponse:
    items = list_ocr_results(pack_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")
    return OcrDocumentListResponse(
        pack_id=pack_id,
        items=[_to_ocr_response(item) for item in items],
    )


@router.post("/{pack_id}/normalize", response_model=NormalizedDocumentListResponse)
async def normalize_pack(pack_id: UUID, _auth_session: CurrentAuthSession) -> NormalizedDocumentListResponse:
    pack = normalize_document_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")
    return NormalizedDocumentListResponse(
        pack_id=pack_id,
        items=[_to_normalized_response(item) for item in pack.normalized_documents],
    )


@router.get("/{pack_id}/normalized-documents", response_model=NormalizedDocumentListResponse)
async def get_normalized_documents(pack_id: UUID, _auth_session: CurrentAuthSession) -> NormalizedDocumentListResponse:
    items = list_normalized_documents(pack_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Document pack not found.")
    return NormalizedDocumentListResponse(
        pack_id=pack_id,
        items=[_to_normalized_response(item) for item in items],
    )
