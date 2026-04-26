from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentFileRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    file_name: str
    stored_path: str
    content_type: str
    size_bytes: int = Field(ge=0)
    uploaded_at: datetime
    sha256: str


class DocumentPackRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    files: list[DocumentFileRecord]
