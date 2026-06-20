# Production Readiness

Last updated: 2026-06-19

## Target Release

The current target is a closed `production pilot` for the validation-only internal pipeline. It is not ready for public SaaS exposure.

The production pilot scope is:

- upload one shipment document pack;
- run OCR, normalization, and deterministic validation;
- review extracted fields, rule results, evidence snippets, and shipment-level notes;
- persist run history and latest reports.

Out of scope for this release:

- landed-cost calculation;
- TN VED assistance;
- logistics advisory;
- public self-serve signup;
- LLM-based extraction or agent workflows.

## Current Validation Gate

Verified on 2026-06-19:

| Gate | Result |
|---|---|
| Backend tests | `96 passed in 9.30s` |
| Frontend TypeScript build | Passed |
| Frontend Vite production build | Passed, `assets/index-Bmb4VhyH.js` about `242.32 kB` before gzip |

Fresh sample-pack runs on the current code:

| Pack | Output | Status | Summary | Current read |
|---|---|---|---|---|
| Aierfuke 05 | `.tmp/validation_run_aierfuke_05_20260611_baseline.json` | `needs_review` | `27 total`, `22 passed`, `0 failed`, `2 warnings`, `0 needs_review`, `3 skipped` | Stable internal-demo baseline. Non-passed results are expected missing contract/payment/expiry conditions. |
| Paini 07 | `.tmp/validation_run_paini_07_20260611_baseline.json` | `needs_review` | `27 total`, `19 passed`, `0 failed`, `2 warnings`, `0 needs_review`, `6 skipped` | Usable after UI cleanup; visible action is mainly COA expiry warning. |
| tianrun 57 | `.tmp/validation_run_tianrun_57_20260611_after_bl_gross_buyer_date_fix.json` | `validated` | `27 total`, `25 passed`, `0 failed`, `0 warnings`, `0 needs_review`, `2 skipped` | Production-pilot baseline after BL gross-weight/date extraction and legal-form normalization fixes; only separate-contract comparisons remain skipped. |
| Denkim 03 | `.tmp/validation_run_denkim_03_20260618_current.json` | `validated` | `27 total`, `22 passed`, `0 failed`, `0 warnings`, `0 needs_review`, `5 skipped` | Now a usable narrow-pilot baseline. COA rotation/OCR reads batch and production date on current code; remaining skips are informational pack gaps rather than hard failures. |
| Hugestone 1 | `.tmp/validation_run_hugestone_1_20260619_policy.json` | `failed` | `27 total`, `21 passed`, `2 failed`, `2 warnings`, `0 needs_review`, `2 skipped` | Extraction is much stronger, and the remaining failure is intentional: draft/incomplete BL signals no BL date and missing container number, while missing separate contract stays informational. |

## Production Blockers

| Blocker | Why it blocks production | Required action |
|---|---|---|
| Current auth is bootstrap/internal-only | The app is protected now, but pilot operations still need clearer user lifecycle, role, and session policy. | Harden bootstrap auth into a pilot-ready access model with explicit admin onboarding/offboarding, session policy, and audit expectations. |
| Synchronous OCR workflow | Larger packs can block requests and make failures hard to retry. | Add background job model or explicitly limit pilot pack size and concurrency. |
| Runtime file retention is undefined | Uploads and OCR outputs will grow and may contain sensitive data. | Define retention, cleanup, backup, and deletion policy. |
| Default local SQLite | SQLite is acceptable for local development, not production pilot history. | Deploy with PostgreSQL and persistent volumes. |
| Frontend/backend deploy packaging is missing | Current app is runnable locally but not reproducibly deployable. | Add Docker/compose or another documented deployment target. |
| Observability is minimal | Failures during OCR/extraction are difficult to operate. | Add structured logs, request/run IDs, and readiness checks. |

## Production Pilot Minimum

Before first real pilot user:

1. Use PostgreSQL via `DYNNO_DATABASE_URL`.
2. Set `DYNNO_ALLOWED_ORIGINS` to the deployed frontend origin only.
3. Serve the frontend with `VITE_DYNNO_API_BASE` pointing at the deployed API.
4. Store `uploads`, OCR temp, and OCR output on explicit persistent volumes.
5. Deploy the existing internal authentication flow with strong admin credentials, session TTL review, and credential rotation guidance.
6. Disable or restrict mock/development endpoints in production mode.
7. Document backup, retention, and deletion behavior for uploaded documents.

## Next Engineering Order

1. Freeze a clean release branch from the current green gate.
2. Add deployment packaging and production environment docs.
3. Add retention/cleanup controls.
4. Harden the current bootstrap/internal auth into a pilot-ready access model.
5. Decide whether the first pilot uses strict synchronous limits or a background worker.
6. Keep `Hugestone 1` as the strict BL/container policy regression while preserving `Aierfuke 05`, `Paini 07`, `tianrun 57`, and `Denkim 03` as extraction baselines.
