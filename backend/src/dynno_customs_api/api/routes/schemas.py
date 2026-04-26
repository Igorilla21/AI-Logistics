from fastapi import APIRouter, HTTPException

from dynno_customs_api.services.schema_registry import list_schema_names, read_schema


router = APIRouter()


@router.get("")
async def get_schema_index() -> dict[str, list[str]]:
    return {"schemas": list_schema_names()}


@router.get("/{schema_name}")
async def get_schema(schema_name: str) -> dict:
    try:
        return read_schema(schema_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
