# Execution Roadmap

Last updated: 2026-06-18

## Current Direction

The current release target remains a `validation-only` internal pipeline. Landed-cost calculation, TN VED assistance, and logistics advisory stay outside the active MVP gate.

Two operating principles are now explicit:

1. Near-term quality should keep improving on real supplier templates that already exist in the repository.
2. Long-term product value requires expanding beyond the current learned templates instead of staying limited to a fixed whitelist forever.

This means the roadmap is:

- `template-first now`;
- `template-robust next`;
- `template-agnostic later`.

## Product Target

### Short-term MVP

The MVP is successful when the system can:

- accept a shipment document pack through the web workflow;
- run OCR, normalization, and deterministic validation end to end;
- work well on the strongest current baselines (`Aierfuke 05`, `Paini 07`, `tianrun 57`);
- distinguish `real document mismatch` from `extraction gap` and `missing source data`.
- stay grounded on the strongest current baselines while preparing for broader template expansion.

### Production Pilot

The first pilot is successful when the system can:

- run on PostgreSQL instead of the default local SQLite runtime;
- protect sensitive document access with internal authentication;
- store runtime files on explicit persistent volumes;
- expose enough logging and operational signals to debug OCR/extraction failures;
- support a narrow but growing set of real-world document layouts without blocking on every new variation.

## Today Plan

### 1. Lock the execution frame

Use this document plus `docs/production-readiness.md` and `docs/mvp-readiness-table.md` as the active operational plan.

Immediate result:

- `validation-only` stays the release scope;
- `PostgreSQL-first` becomes the default path for runtime and future auth;
- broader template expansion remains a confirmed product direction, but the exact handling policy for unknown layouts is still open.

### 2. Stabilize the current baseline

Before new platform work, review the current dirty worktree and separate:

- already-ready changes;
- in-progress changes;
- release-blocking changes;
- Denkim/Hugestone hardening work.

Immediate checks:

- inspect modified backend/frontend files;
- avoid treating the current worktree as a frozen release baseline;
- keep `Aierfuke 05`, `Paini 07`, and `tianrun 57` as regression anchors.

### 3. Switch runtime planning to PostgreSQL-first

From this point, new deployment and auth work should target PostgreSQL, not the default SQLite runtime.

Immediate execution order:

1. Provision local PostgreSQL for the project.
2. Set `DYNNO_DATABASE_URL` in `backend/.env`.
3. Run Alembic against PostgreSQL.
4. Verify backend startup and table creation on PostgreSQL.
5. Only after that, add auth tables and auth flows.

### 4. Auth on PostgreSQL is now in place

The first internal auth layer is already implemented on top of SQL persistence with `users` and `auth_sessions`.

What remains is pilot-hardening rather than greenfield auth work:

- bootstrap/admin lifecycle policy;
- stronger role model if the pilot grows beyond one small internal team;
- session retention, revocation, and audit expectations;
- deployment-time secret and credential handling.

### 5. Denkim status after the platform baseline is aligned

A fresh end-to-end rerun on 2026-06-18 saved to `.tmp/validation_run_denkim_03_20260618_current.json` returned `validated`.

Current verified Denkim read:

- `R019` and `R020` now pass; the current OCR rotation retry reads the COA well enough to extract `batch_no` and `manufacture_date`;
- `R014` is no longer a hard failure; current behavior skips it when empty package tare is absent but palletized gross/net reconciliation still holds;
- remaining non-passed items are informational skips (`R002`, `R003`, `R005`, `R006`, `R014`) rather than hard extraction blockers.

## Next 2 Weeks

### Track A: Quality on known packs

Priority order:

1. Hugestone BL/COA/packing extraction hardening.
2. Keep `Denkim 03` as a regression baseline on the current pipeline.
3. Decide whether the current `R014` informational-skip policy is acceptable for the first pilot or needs explicit operator confirmation.
4. Regression reruns on `Aierfuke 05`, `Paini 07`, `tianrun 57`, and `Denkim 03`.

### Track B: Broader template expansion

Priority order:

1. Improve weak document classification behavior.
2. Strengthen label-based and line-aware fallback extraction paths.
3. Reduce supplier-specific assumptions where broader field-level logic is possible.
4. Keep each new real pack as a regression fixture for future extraction expansion.

## MVP-to-Pilot Roadmap

### Phase 1: Narrow MVP hardening

- stabilize current validation workflow;
- reduce false mismatches on known packs;
- keep manual-review output readable on weaker packs;
- document current known limitations honestly.

### Phase 2: Pilot platform baseline

- PostgreSQL runtime;
- internal auth;
- deploy packaging;
- persistent volumes for uploads and OCR outputs;
- retention and cleanup rules;
- minimal observability.

### Phase 3: Production-readiness expansion

- background workers or a deliberate synchronous operating policy;
- stronger audit trail and role model;
- repeatable onboarding flow for new supplier templates;
- regression-fixture loop for every newly seen real pack.

## Denkim Next

The next Denkim-specific pass should answer these narrower questions:

1. Is the validated 2026-06-18 Denkim rerun stable enough to keep as a standing regression baseline after future extraction changes?
2. Is the current `R014` skip semantics acceptable for the pilot and for the UI copy shown to operators?
3. Can any remaining informational skips (`R002`, `R003`, `R005`, `R006`) be reduced further from source data already present in the pack, or are they true pack-level gaps?
4. Once Denkim is held stable, should `Hugestone 1` become the main weak-template hardening priority?

## Working Rule

Every new real pack should be treated as both:

- a business validation case;
- a regression asset for expanding template coverage.

The long-term goal is not a fixed whitelist of templates. The confirmed direction is to keep expanding real-world template coverage from new packs while preserving a stable validation baseline on the strongest current cases.
