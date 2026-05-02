# Dynno Customs

Internal web application for customs document validation and landed-cost workflows.

## Repository Layout

- `backend` - FastAPI application
- `frontend` - React/Vite web client
- `schemas` - JSON Schema contracts for extraction and validation
- `docs` - product, validation, and architecture documents

## Architecture Direction

- Web interface for operators and reviewers
- Backend API for upload, extraction orchestration, validation, and reporting
- Background workers for OCR and rule execution
- Self-hosted deployment model for sensitive document handling

## Local Development

### Backend

1. Create a project-local virtual environment:
   `py -m venv backend/.venv`
2. Activate it:
   `backend\\.venv\\Scripts\\Activate.ps1`
3. Install dependencies:
   `python -m pip install -e backend[dev]`
4. Run the API:
   `uvicorn dynno_customs_api.main:app --app-dir backend/src --reload`

### Frontend

The frontend scaffold is prepared manually because `node/npm` were not usable in the current environment at scaffold time.

When Node.js is available:

1. `cd frontend`
2. `npm install`
3. `npm run dev`

## Current Status

- Product roadmap documented
- Validation specification documented
- Field catalog documented
- JSON Schemas defined
- Initial backend/frontend scaffold created
- Backend rule engine runner implemented for validation rules `R001`-`R027`
