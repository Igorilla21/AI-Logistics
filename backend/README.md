# Backend

FastAPI service for:

- document pack intake
- schema discovery
- extraction orchestration
- validation orchestration
- report delivery
- rule execution

OCR, persistent storage, and auth are not wired yet.

## Validation

- `POST /api/validation/reports/{pack_id}` runs validation rules against a document pack.
- If the pack has no normalized documents yet, the endpoint runs the current normalization stub first.
- `POST /api/validation/reports/mock` remains available for response-shape checks.
