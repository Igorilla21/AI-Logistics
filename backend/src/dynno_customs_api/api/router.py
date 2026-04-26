from fastapi import APIRouter

from dynno_customs_api.api.routes import document_packs, health, schemas, validation


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(schemas.router, prefix="/schemas", tags=["schemas"])
api_router.include_router(document_packs.router, prefix="/document-packs", tags=["document-packs"])
api_router.include_router(validation.router, prefix="/validation", tags=["validation"])
