from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from uuid import UUID

from dynno_customs_api.models.domain import ValidationReportRecord


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


validation_report_store = InMemoryValidationReportStore()
