# MVP Readiness Table

Last updated: 2026-06-20

Scope: validation-only internal pipeline. Cost calculator, logistics advisory, TN VED support, and LLM assistance are outside the current MVP gate.

## Current Baseline

| Sample pack | Source | Run response | Workflow status | Rule summary | Current read |
|---|---|---|---|---|---|
| Aierfuke 05 | `тестовые доки/Aierfuke 05` | `.tmp/validation_run_aierfuke_05_20260611_baseline.json` | `needs_review` | `27 total`, `22 passed`, `0 failed`, `2 warnings`, `0 needs_review`, `3 skipped` | Stable internal-demo baseline. Remaining non-passed items are expected document/business conditions: missing separate contract, missing payment confirmation, and absent COA expiry date. |
| Paini 07 | `тестовые доки/Paini 07` | `.tmp/validation_run_paini_07_20260611_baseline.json` | `needs_review` | `27 total`, `19 passed`, `0 failed`, `2 warnings`, `0 needs_review`, `6 skipped` | Usable after UI cleanup. Skipped contract/incoterms/BL package-container checks are shipment-level informational; the visible action is mainly `R021` COA expiry warning. |
| tianrun 57 | `тестовые доки/tianrun 57` | `.tmp/validation_run_tianrun_57_20260611_after_bl_gross_buyer_date_fix.json` | `validated` | `27 total`, `25 passed`, `0 failed`, `0 warnings`, `0 needs_review`, `2 skipped` | Production-pilot baseline after BL gross-weight/date extraction and legal-form normalization fixes. Remaining skipped items are expected missing separate-contract comparisons. |

## Additional Sample Pack Runs

| Sample pack | Source | Run response | Workflow status | Rule summary | Current read |
|---|---|---|---|---|---|
| Denkim 03 | `тестовые доки/Denkim 03` | `.tmp/validation_run_denkim_03_20260618_current.json` | `validated` | `27 total`, `22 passed`, `0 failed`, `0 warnings`, `0 needs_review`, `5 skipped` | Current narrow-pilot baseline. COA rotation/OCR now recovers batch and production date; remaining skips are informational contract/incoterms/buyer gaps plus `R014` when empty package tare is absent but palletized reconciliation still works. |
| Hugestone 1 | `тестовые доки/Hugestone 1` | `.tmp/validation_run_hugestone_1_20260620_r017_policy.json` | `failed` | `27 total`, `21 passed`, `3 failed`, `1 warning`, `0 needs_review`, `2 skipped` | Extraction is now mostly usable, but the pack correctly fails because the BL appears draft/incomplete and the container number is absent from the packing/BL checks. Missing separate contract stays an informational skip, and missing payment confirmation remains a warning. |

## Aierfuke 05 Document Readiness

| Document | File | Extracted coverage | Status | Notes |
|---|---|---|---|---|
| Addendum | `1. Add 05 signed.pdf` | Buyer, seller, contract no/date, addendum no/date, payment terms, incoterms | Stable | Contract/addendum/payment/incoterms fields are usable for rule checks. |
| Invoice | `2. CI -05.pdf` | Shipper, buyer, manufacturer, contract no, addendum no, invoice no/date, payment terms, incoterms, currency, total amount, line item | Stable | `payment_terms` now reads from clean embedded PDF text: `100% T/T IN ADVANCE.` |
| Packing list | `3.  PL-05.pdf` | Shipper, buyer, manufacturer, contract no, addendum no, invoice no, container no, gross/net/package weights, empty bag weight, package type/count, line item | Stable | Company and contract fields now prefer the clean embedded PDF text layer over noisy OCR. |
| Certificate of origin | `4. CO.pdf` | Exporter/shipper, buyer/consignee, invoice no/date, gross weight, origin country | Stable enough | Company name still has minor OCR spelling drift, but cross-document matching tolerates it. |
| COA | `5. COA of industry grade.pdf` | Manufacturer, batch no, manufacture date | Stable with expected gap | `expiry_date` is absent in source, so `R021` is warning-level and `R023` remains skipped. |
| MBL | `6. LED417527A.pdf` | Shipper, consignee/buyer, container no, gross weight, package count, BL no/date, cargo description | Stable | `shipper_name` now resolves cleanly to `HENAN AIERFUKE CHEMICALS CO.,LTD`. |

## Aierfuke 05 Rule Readiness

| Rule area | Rules | Current status | Classification | Action |
|---|---|---|---|---|
| Party matching | `R001`, `R002` | Passed | Stable extraction | Keep as regression baseline for OCR/name normalization. |
| Product and commercial consistency | `R004`, `R006`, `R007`, `R008`, `R009` | Passed | Stable extraction | Keep as baseline; add more products/templates before declaring broad coverage. |
| Packing/weight checks | `R010` through `R017`, `R024` | Passed | Stable extraction | Current Aierfuke packing and BL gross-weight logic is usable for this template. |
| COA batch/date checks | `R019`, `R020`, `R022` | Passed | Stable extraction | `expiry_date` remains optional-warning behavior for this pack. |
| Contract cross-checks | `R003`, `R005` | Skipped | Real document-pack gap | Pack has no separate contract document. This is not an OCR issue. |
| Payment confirmation | `R018` | Warning-level failed | Real document-pack issue | Add payment confirmation to pass when prepayment is required. |
| COA expiry date | `R021`, `R023` | Warning/skipped | Real source-data gap | Source COA has manufacture date but no expiry date. Current behavior is acceptable for MVP if warning is intentional. |

## Paini 07 Snapshot

| Document | File | Extracted coverage | Status | Notes |
|---|---|---|---|---|
| Addendum | `1. Add 07 signed.pdf` | Buyer, seller, contract no/date, addendum no/date, payment terms, incoterms | Stable enough | Bilingual addendum mapping now resolves `Shandong Paini New Material Co., Ltd`, `Soyuzopthim Ltd`, contract date `15.03.2024`, and `Prepayment 100%`. |
| Invoice | `2. Inv.pdf` | 11 fields, 1 line item | Stable enough | Invoice no/date, contract/addendum refs, PNA-TAD line item, total amount, buyer, shipper, and manufacturer now extract. |
| Packing list | `3. PL.pdf` | 15 fields, 1 line item | Stable enough | DRUMS quantity now prefers the clean text-layer value `136`; because pallet weight is absent in source, drum tare is derived as `21 kg` and pallet tare as `15 kg`. |
| MBL | `4. BL.pdf` | 6 fields | Partial | BL number, date, buyer, and gross weight extract; package quantity and container number are still missing from this BL OCR/table layout. |
| Certificate of origin | `5. COO.pdf`, `6.CO Copy.pdf` | 7 fields each | Partial | Both files classify as certificate of origin; duplication/selection behavior should be reviewed. |
| COA | `7. COA 1.pdf`, `8. COA 2.pdf` | 3 fields / 2 fields | Partial | Batch extraction works; first COA manufacture/analysis date extracts, second COA still misses manufacture date due noisier label layout. |

| Rule area | Rules | Current status | Classification | Action |
|---|---|---|---|---|
| Party and commercial matching | `R001` through `R009` | Passed/skipped | Stable extraction with expected contract gaps | `R002` no longer warns after addendum buyer/seller mapping fix; remaining skips are due the missing separate contract document. |
| Packing and weight checks | `R010`, `R011`, `R014`, `R015`, `R016` | Passed | Derived packaging logic | For `DRUM + PALLETS`, use default drum tare `21 kg` and derive pallet tare from the remaining gross-minus-net weight. |
| Payment confirmation | `R018` | Warning-level failed | Real document-pack or classification gap | Confirm whether payment confirmation is absent; if present under another filename, add classification/mapping. |
| COA batch/date checks | `R019`, `R020`, `R021`, `R022`, `R023` | Batch/manufacture mostly fixed; expiry still warning/skipped | Real source-data gap plus one noisy COA label | Keep expiry as warning when manufacture exists; improve second COA analysis-date label later. |
| BL cross-checks | `R024`, `R025`, `R026` | Gross-weight check fixed; package quantity may still skip, while container gaps are strict when BL and packing list are present | BL table/source-data gap | Improve BL package quantity extraction if source contains readable values; missing container number is now a visible document issue. |

## tianrun 57 Snapshot

| Document | File | Extracted coverage | Status | Notes |
|---|---|---|---|---|
| Addendum | `1. Add 57 s.pdf` | 8 fields | Stable enough | Addendum fields are usable for the current rule set. |
| Invoice | `2. INVOICE.pdf` | 8 fields, 1 line item | Stable enough | Invoice extraction is close to MVP-ready for this template. |
| MBL | `4. FASTGT1911WVRA320-OB.pdf` | 7 fields | Stable enough | BL classification works; BL number/date, buyer, gross weight, package quantity, and container number now feed the cross-document checks. |
| Packing list | `4. PACKING LIST.pdf` | 12 fields, 1 line item | Stable enough | Packing-list extraction is strong on this pack. |
| COA | `5. COA.pdf` | 5 fields | Stable enough | COA has enough coverage for most checks, but date cross-checking still skipped where BL/manufacture date is missing. |
| Russian invoice/contract-like document | `6. Счет на оплату (с договором) № СОХ096.1 от 02.10.2025.pdf` | 2 fields, 0 line items | Deferred mapping gap | Currently classifies as invoice; not required for the validated baseline because the separate contract document is still absent from the pack. |

| Rule area | Rules | Current status | Classification | Action |
|---|---|---|---|---|
| Party matching | `R001`, `R002` | Passed | Stable enough | `OOO`/`ООО`/`LLC` legal-form prefixes are ignored during normalized party comparison. |
| Contract/date cross-checks | `R003`, `R005` | Skipped | Real document-pack gap | Pack has no separate contract document. This is not an extraction blocker for the current baseline. |
| COA/BL date and weight checks | `R022`, `R024` | Passed | Stable extraction | BL date now extracts from ISO date text and gross weight prefers cargo table values over legal-address/INN noise. |
| Remaining core rules | Most other rules | Passed | Strong baseline | Keep as regression target while Denkim/Hugestone are hardened. |

## MVP Gate View

| Area | Current state | MVP readiness | Next check |
|---|---|---|---|
| Intake and orchestration | Files upload through `POST /api/validation-runs`; OCR, normalization, validation, and latest-run storage complete synchronously. | Usable for internal MVP demos. | Worker/queue is not required for first internal validation, but will be needed before production load. |
| OCR provider boundary | Current provider is Tesseract with embedded PDF text fallback and provider abstraction in place. | Ready for Google Document AI experiment. | Add provider adapter behind existing registry, then compare same sample packs side by side. |
| Extraction | Aierfuke 05, Paini 07, tianrun 57, and Denkim 03 are usable for a narrow internal pilot on the current code. Hugestone 1 now exposes real pack/document defects rather than broad extraction failure. | Internal pilot can proceed with a narrow supported-template statement that includes Denkim 03. Public/production coverage is not ready. | Keep Denkim as a regression baseline, and use Hugestone as the strict BL/container policy check. |
| Rule engine | Core rule runner handles `R001` through `R027`; current failures on new packs look mostly extraction/source-data driven rather than missing rule implementations. | Ready as a deterministic rule layer for supported templates, but release notes must distinguish real document issues from extraction gaps. | Add regression fixtures for each fixed supplier-template gap. |
| Frontend review UI | Shipment workspace can display status, document cards, issues, extracted fields, and evidence. | Good enough for internal MVP walkthrough. | After more backend samples, add any missing issue labels or review states surfaced by real data. |

## Next Sample Runs

Recommended order:

1. Keep Hugestone 1 as a regression for strict BL/container policy: missing separate contract is informational, but missing BL date/container number is visible and strict.
2. Decide whether the current Denkim-style `R014`/`R016` informational handling for source-missing tare is acceptable for the first pilot or needs explicit operator confirmation.
3. Keep rerunning `Denkim 03` after extraction changes so the current validated state stays locked as a regression baseline.
4. Run one pack likely to include payment confirmation or a complete COA expiry date, so `R018` and `R021` can be tested as true passes.

## Open MVP Risks

| Risk | Why it matters | Current mitigation |
|---|---|---|
| Template coverage varies sharply by supplier | Aierfuke, Paini, tianrun, and Denkim are usable narrow baselines; Hugestone still shows broad extraction gaps. | Keep supplier-specific regressions and narrow the first production pilot to supported templates until Hugestone and future weak-template cases are hardened. |
| OCR quality differs by source PDF | Tesseract plus embedded text fallback works on Aierfuke, but scanned-only PDFs may behave differently. | Keep current Tesseract pipeline, then compare Google Document AI on the same packs. |
| Some skipped rules are caused by missing document types | This is correct behavior, but the UI must make it obvious to users. | Frontend already shows skipped/warning states; review copy may need tuning after more real runs. |
| Synchronous workflow can block on larger packs | Internal MVP is acceptable, but production will need background jobs. | Defer queue/worker until validation accuracy stabilizes. |
