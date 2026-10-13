import asyncio
import json
import os

from property_key_drill.drill_workflow import run_leaked_key_drill
from property_key_drill.infrai_client import InfraiClient
from property_key_drill.models import (
    DrillRequest,
    InspectionReminder,
    MaintenanceRequest,
    TenantDocument,
)


async def main() -> None:
    request = DrillRequest(
        property_id="cedar-court-14",
        maintenance_requests=[
            MaintenanceRequest(
                request_id="maint-1042",
                property_id="cedar-court-14",
                summary="Kitchen tap inspection",
            )
        ],
        tenant_documents=[
            TenantDocument(
                document_id="doc-88",
                property_id="cedar-court-14",
                kind="lease",
            )
        ],
        inspection_reminders=[
            InspectionReminder(
                reminder_id="inspect-31",
                property_id="cedar-court-14",
                due_on="2026-10-15",
            )
        ],
    )
    client = InfraiClient(api_key=os.environ["INFRAI_API_KEY"])
    try:
        result = await run_leaked_key_drill(client, request)
        print(json.dumps(result.model_dump(), indent=2))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
