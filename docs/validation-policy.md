# Validation Policy

Last updated: 2026-06-19

## Purpose

This policy defines how validation results should distinguish real document problems from checks that cannot or should not be evaluated.

The core rule is:

`skipped` is acceptable only when the missing information is not critical for the package decision.

If a required final document is present but a critical field is absent, the result must be visible as a `failed` issue, not hidden as an informational skip.

## Result Classes

| Class | When to use | Operator meaning |
|---|---|---|
| `passed` | The rule had enough reliable inputs and the check succeeded. | No action needed. |
| `failed` + `error` | Critical required information is missing, inconsistent, or invalid. | The package is not ready without correction or replacement documents. |
| `failed` + `warning` | Important but non-blocking information is missing or inconsistent. | The package can be reviewed, but the operator should decide whether follow-up is needed. |
| `skipped` informational | The rule cannot run because non-critical information or an optional reference document is absent. | No document-level issue; show as a pack note or audit trace. |
| `needs_review` | Inputs exist but are ambiguous, low-confidence, or conflicting at extraction time. | Operator must inspect the evidence before relying on the result. |

## Informational Skip Rules

Use informational `skipped` only when all of these are true:

- The missing input is not critical for deciding whether the current document pack is usable.
- The absence is expected for some real packs or optional scenarios.
- Showing a document-level issue would create noise rather than a useful action.
- The result still remains visible in audit/report data as a pack note or trace.

Current examples:

- `R003` and `R005`: no separate master contract document is included, so contract-dependent comparisons cannot run. This is not a blocker when addendum and invoice values are otherwise extracted.
- `R006`: Incoterms comparison is skipped when only one required value is available and there is no mismatch to evaluate.
- `R023`: expiry-after-manufacture comparison is skipped when the primary missing-expiry signal is already covered by `R021`.
- `R025`: BL vs packing-list package quantity can remain skipped while package meaning is ambiguous across `bags`, `pallets`, and `packages`.

## Strict Missing Data

Do not use informational `skipped` when the missing value is critical for a final document.

Current examples:

- `R017`: packing list container number is a visible warning when absent.
- `R019` and `R020`: COA batch number and manufacture date are critical and must fail when absent.
- `R022`: if a BL document exists and COA manufacture date exists, missing `bl_date` is an `error` because the BL may be draft or incomplete.
- `R026`: if BL and packing list are present, missing container number in either document is an `error`.

## UI Policy

The UI should separate:

- `Issues`: `failed` errors and warning-level failures that require operator attention.
- `Needs review`: ambiguous or low-confidence extracted values.
- `Pack notes`: informational skips and optional context.

Informational skips should not turn document cards yellow or red by themselves. Strict missing-data failures must remain visible in document cards, recent alerts, next action, and rule details.

## Rule Authoring Checklist

Before adding or changing a rule, decide:

1. Is this field/document critical for package readiness?
2. If the document exists but the field is missing, should the operator act?
3. Is absence expected and non-critical for some real packs?
4. Would hiding the result as a pack note reduce noise without hiding risk?
5. Which existing sample pack should lock the behavior as a regression?
