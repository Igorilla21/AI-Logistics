from dynno_customs_api.models.api import (
    EvidenceResponse,
    NormalizedDocumentResponse,
    ValidationReportResponse,
    ValidationRunResponse,
    ValidationRunSummaryResponse,
    ValidationResultGroups,
    ValidationResultResponse,
    ValidationSummary,
)
from dynno_customs_api.models.domain import NormalizedDocumentRecord, ValidationReportRecord
from dynno_customs_api.services.validation_workflow import ValidationWorkflowResult


def to_normalized_document_response(document: NormalizedDocumentRecord) -> NormalizedDocumentResponse:
    return NormalizedDocumentResponse(
        schema_version=document.schema_version,
        document_id=document.document_id,
        document_type=document.document_type,
        source_file_name=document.source_file_name,
        source_file_path=document.source_file_path,
        mime_type=document.mime_type,
        pages=document.pages,
        language=document.language,
        raw_text_ref=document.raw_text_ref,
        extraction_status=document.extraction_status,
        fields=document.fields.model_dump(exclude_none=True),
        line_items=[item.model_dump(exclude_none=True) for item in document.line_items],
        evidence=[
            EvidenceResponse(
                document_type=item.document_type,
                page_no=item.page_no,
                field_name=item.field_name,
                text_snippet=item.text_snippet,
                confidence=item.confidence,
            )
            for item in document.evidence
        ],
        metadata=document.metadata.model_dump(exclude_none=True),
    )


def to_validation_report_response(report: ValidationReportRecord) -> ValidationReportResponse:
    return ValidationReportResponse(
        schema_version=report.schema_version,
        report_id=report.report_id,
        pack_id=report.pack_id,
        generated_at=report.generated_at,
        summary=ValidationSummary(**report.summary.model_dump()),
        results=[
            ValidationResultResponse(
                rule_code=result.rule_code,
                severity=result.severity,
                status=result.status,
                message=result.message,
                documents=result.documents,
                fields=result.fields,
                observed_values=result.observed_values,
                expected_values=result.expected_values,
                evidence=[
                    EvidenceResponse(
                        document_type=item.document_type,
                        page_no=item.page_no,
                        field_name=item.field_name,
                        text_snippet=item.text_snippet,
                        confidence=item.confidence,
                    )
                    for item in result.evidence
                ],
                confidence=result.confidence,
                created_at=result.created_at,
            )
            for result in report.results
        ],
    )


def group_validation_results(report: ValidationReportRecord) -> ValidationResultGroups:
    groups = ValidationResultGroups()
    for result in to_validation_report_response(report).results:
        if result.status == "failed" and result.severity == "warning":
            groups.warnings.append(result)
        elif result.status == "failed":
            groups.failed.append(result)
        elif result.status == "needs_review":
            groups.needs_review.append(result)
        elif result.status == "skipped":
            groups.skipped.append(result)
        elif result.status == "passed":
            groups.passed.append(result)
    return groups


def to_validation_run_response(result: ValidationWorkflowResult) -> ValidationRunResponse:
    report_response = to_validation_report_response(result.report)
    return ValidationRunResponse(
        run_id=result.report.report_id,
        pack_id=result.pack.pack_id,
        status=result.pack.status,
        created_at=result.pack.created_at,
        updated_at=result.pack.updated_at,
        summary=report_response.summary,
        grouped_results=group_validation_results(result.report),
        report=report_response,
        documents=[to_normalized_document_response(item) for item in result.pack.normalized_documents],
    )


def to_validation_run_summary_response(result: ValidationWorkflowResult) -> ValidationRunSummaryResponse:
    report_response = to_validation_report_response(result.report)
    return ValidationRunSummaryResponse(
        run_id=result.report.report_id,
        pack_id=result.pack.pack_id,
        status=result.pack.status,
        created_at=result.pack.created_at,
        updated_at=result.pack.updated_at,
        generated_at=result.report.generated_at,
        summary=report_response.summary,
        document_count=len(result.pack.normalized_documents),
        file_names=[item.file_name for item in result.pack.files],
    )
