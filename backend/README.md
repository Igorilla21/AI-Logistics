# Backend

FastAPI service for:

- document pack intake
- schema discovery
- extraction orchestration
- validation orchestration
- report delivery
- rule execution

OCR, persistent storage, and auth are not wired yet.

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
- `GET /api/document-packs/{pack_id}/ocr-results` returns the latest in-memory OCR results for the pack.
- Completed OCR runs persist raw text under `storage/ocr/{pack_id}/{document_id}.txt` and expose that path as `raw_text_ref`.
- The first text extractor reads `raw_text_ref` during normalization and extracts MVP fields for invoice, packing list, and bill of lading documents.

## Validation

- `POST /api/validation/reports/{pack_id}` runs validation rules against a document pack.
- If the pack has no normalized documents yet, the endpoint runs the current normalization stub first.
- `POST /api/validation/reports/mock` remains available for response-shape checks.
