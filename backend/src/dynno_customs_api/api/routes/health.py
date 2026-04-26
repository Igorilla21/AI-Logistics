from datetime import UTC, datetime

from fastapi import APIRouter

from dynno_customs_api.config import settings


router = APIRouter()


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(UTC).isoformat(),
    }
