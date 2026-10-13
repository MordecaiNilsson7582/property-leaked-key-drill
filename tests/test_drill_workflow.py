import asyncio
from typing import Any

from property_key_drill.drill_workflow import run_leaked_key_drill
from property_key_drill.models import (
    DrillRequest,
    InspectionReminder,
    MaintenanceRequest,
    TenantDocument,
)


class RecordingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    async def create_drill_key(self, idempotency_key: str) -> dict[str, str]:
        self.calls.append(("create", idempotency_key))
        return {"key_id": "key-drill-7", "key_secret": "one-time-value"}

    async def report_compromise(self, key_id: str) -> None:
        self.calls.append(("report", key_id))

    async def search_logs(self) -> list[dict[str, str]]:
        self.calls.append(("logs",))
        return [
            {"message": "read cedar-court-14 lease"},
            {"message": "read maple-house-2 inspection"},
        ]

    async def rotate_key(
        self, key_id: str, grace_hours: int, idempotency_key: str
    ) -> dict[str, str]:
        self.calls.append(("rotate", key_id, grace_hours, idempotency_key))
        return {
            "key": "ifr_replacement_secret_0008",
            "key_id": "ifr_replacem...",
            "old_key_id": key_id,
        }

    async def revoke_key(self, key_id: str) -> None:
        self.calls.append(("revoke", key_id))


class FailingClient(RecordingClient):
    async def search_logs(self) -> list[dict[str, str]]:
        self.calls.append(("logs",))
        raise RuntimeError("log search failed")


def test_drill_reports_before_searching_and_rotating() -> None:
    client = RecordingClient()
    request = DrillRequest(
        property_id="cedar-court-14",
        grace_hours=2,
        maintenance_requests=[
            MaintenanceRequest(
                request_id="maint-1",
                property_id="cedar-court-14",
                summary="Boiler check",
            )
        ],
        tenant_documents=[
            TenantDocument(
                document_id="doc-1", property_id="cedar-court-14", kind="lease"
            )
        ],
        inspection_reminders=[
            InspectionReminder(
                reminder_id="rem-1",
                property_id="cedar-court-14",
                due_on="2026-10-15",
            )
        ],
    )

    result = asyncio.run(
        run_leaked_key_drill(client, request)  # type: ignore[arg-type]
    )

    assert [call[0] for call in client.calls] == [
        "create",
        "report",
        "logs",
        "rotate",
        "revoke",
        "revoke",
    ]
    assert client.calls[-2:] == [
        ("revoke", "ifr_...0008"),
        ("revoke", "key-drill-7"),
    ]
    assert result.status == "confirmed"
    assert result.log_matches == 1
    assert result.maintenance_requests_reviewed == 1
    assert result.tenant_documents_reviewed == 1
    assert result.inspection_reminders_reviewed == 1
    assert result.old_key_revoked is True


def test_drill_revokes_created_key_when_an_intermediate_step_fails() -> None:
    client = FailingClient()

    try:
        asyncio.run(run_leaked_key_drill(client, DrillRequest(property_id="property-1")))  # type: ignore[arg-type]
    except RuntimeError as exc:
        assert str(exc) == "log search failed"
    else:
        raise AssertionError("expected log search failure")

    assert [call[0] for call in client.calls] == [
        "create",
        "report",
        "logs",
        "revoke",
    ]
