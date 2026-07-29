from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from uuid import UUID

from sqlalchemy import delete, desc, insert, select, update

from dynno_customs_api.models.domain import ValidationReportRecord, ValidationResultRecord
from dynno_customs_api.services.database import get_engine, validation_reports_table, validation_results_table


@dataclass(slots=True)
class InMemoryValidationReportStore:
    _latest_by_pack_id: dict[UUID, ValidationReportRecord] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def save(self, report: ValidationReportRecord) -> ValidationReportRecord:
        with self._lock:
            self._latest_by_pack_id[report.pack_id] = report
        return report

    def get_latest(self, pack_id: UUID) -> ValidationReportRecord | None:
        with self._lock:
            return self._latest_by_pack_id.get(pack_id)


class SqlValidationReportStore:
    def save(self, report: ValidationReportRecord) -> ValidationReportRecord:
        payload = report.model_dump(mode="json")
        values = {
            "report_id": str(report.report_id),
            "pack_id": str(report.pack_id),
            "generated_at": report.generated_at,
            "payload": payload,
        }

        with get_engine().begin() as connection:
            existing = connection.execute(
                select(validation_reports_table.c.report_id).where(
                    validation_reports_table.c.report_id == str(report.report_id)
                )
            ).scalar_one_or_none()

            if existing is None:
                connection.execute(insert(validation_reports_table).values(**values))
            else:
                connection.execute(
                    update(validation_reports_table)
                    .where(validation_reports_table.c.report_id == str(report.report_id))
                    .values(**values)
                )

            connection.execute(
                delete(validation_results_table).where(validation_results_table.c.report_id == str(report.report_id))
            )

            if report.results:
                connection.execute(
                    insert(validation_results_table),
                    [
                        {
                            "report_id": str(report.report_id),
                            "pack_id": str(report.pack_id),
                            "rule_code": item.rule_code,
                            "status": item.status,
                            "severity": item.severity,
                            "created_at": item.created_at,
                            "payload": item.model_dump(mode="json"),
                        }
                        for item in report.results
                    ],
                )

        return report

    def get_latest(self, pack_id: UUID) -> ValidationReportRecord | None:
        with get_engine().begin() as connection:
            row = connection.execute(
                select(validation_reports_table.c.report_id, validation_reports_table.c.payload)
                .where(validation_reports_table.c.pack_id == str(pack_id))
                .order_by(desc(validation_reports_table.c.generated_at))
                .limit(1)
            ).one_or_none()

        if row is None:
            return None

        with get_engine().begin() as connection:
            result_rows = connection.execute(
                select(validation_results_table.c.payload)
                .where(validation_results_table.c.report_id == row.report_id)
                .order_by(
                    validation_results_table.c.created_at,
                    validation_results_table.c.rule_code,
                )
            ).all()

        return self._build_report_from_rows(row.payload, result_rows)

    def clear(self) -> None:
        with get_engine().begin() as connection:
            connection.execute(delete(validation_results_table))
            connection.execute(delete(validation_reports_table))

    @staticmethod
    def _build_report_from_rows(payload: dict, result_rows: list[object]) -> ValidationReportRecord:
        results = [ValidationResultRecord.model_validate(row.payload) for row in result_rows]
        base_report = ValidationReportRecord.model_validate(payload)
        return base_report.model_copy(update={"results": results})


validation_report_store = SqlValidationReportStore()
