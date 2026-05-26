# Backend

FastAPI service for:

- document pack intake
- schema discovery
- extraction orchestration
- validation orchestration
- report delivery
- rule execution

OCR and SQL-backed persistence are wired. Auth is not implemented yet.

## Persistence

- Runtime persistence uses SQLAlchemy tables for `document_packs`, `document_files`, `ocr_document_results`, `normalized_documents`, `validation_reports`, and `validation_results`.
- The default local runtime database is repo-local SQLite at `storage/dynno_customs.db`.
- Local PostgreSQL can be enabled by setting `DYNNO_DATABASE_URL` in `backend/.env`.
- Schema migrations are managed with Alembic under `backend/alembic/`.
- Application startup runs `alembic upgrade head` before serving requests.

Typical Alembic commands from `backend/`:

```powershell
.\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
.\.venv\Scripts\alembic.exe -c alembic.ini current
.\.venv\Scripts\alembic.exe -c alembic.ini revision -m "describe change"
```

If an existing local database was created before Alembic was introduced, align it to the baseline revision once:

```powershell
.\.venv\Scripts\alembic.exe -c alembic.ini stamp head
```

## OCR Settings

The Tesseract OCR integration uses these backend settings:

- `DYNNO_TESSERACT_CMD` - Tesseract executable path or command name. Default: `C:\Program Files\Tesseract-OCR\tesseract.exe` on Windows when present, otherwise `tesseract`.
- `DYNNO_OCR_LANGS` - Tesseract language set. Default: `eng+rus`.
- `DYNNO_OCR_PDF_DPI` - PDF page render DPI before OCR. Default: `300`.
- `DYNNO_OCR_TEMP_DIR` - repo-local temporary OCR directory. Default: `.tmp/ocr`.
- `DYNNO_OCR_OUTPUT_DIR` - repo-local OCR output directory. Default: `storage/ocr`.

On Windows, if Tesseract is not in `PATH`, set:

```powershell
$env:DYNNO_TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

The OCR adapter service is implemented in `dynno_customs_api.services.tesseract_ocr`.
It accepts stored PDF/image document records and returns page-level raw text with OCR confidence.

- `POST /api/document-packs/{pack_id}/ocr` runs OCR for all files in a document pack.
- `GET /api/document-packs/{pack_id}/ocr-results` returns the latest persisted OCR results for the pack.
- Completed OCR runs persist raw text under `storage/ocr/{pack_id}/{document_id}.txt` and expose that path as `raw_text_ref`.
- The first text extractor reads `raw_text_ref` during normalization and extracts MVP fields for invoice, packing list, bill of lading, addendum, COA, and payment confirmation documents.

## Validation

- `POST /api/validation-runs` accepts files, then runs intake, OCR, normalization, rule-engine validation, and returns one workflow response with the report, normalized documents, summary, and grouped results.
- `GET /api/validation-runs` returns saved validation-run history from persisted packs and latest reports.
- `GET /api/validation-runs/{pack_id}` returns the latest persisted validation run response for a document pack.
- `POST /api/validation/reports/{pack_id}` runs validation rules against a document pack.
- If the pack has no normalized documents yet, the endpoint runs the current normalization stub first.
- `POST /api/validation/reports/mock` remains available for response-shape checks.
