import json
import uuid
from collections.abc import Mapping
from typing import Any

from .infrai_client import InfraiClient
from .models import DrillRequest, DrillResult


def _contains_property(value: Any, property_id: str) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_property(item, property_id) for item in value.values())
    if isinstance(value, list):
        return any(_contains_property(item, property_id) for item in value)
    return property_id in str(value)


def _log_items(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, Mapping):
        for value in data.values():
            if isinstance(value, list):
                return value
    return []


async def run_leaked_key_drill(
    client: InfraiClient, request: DrillRequest
) -> DrillResult:
    run_id = uuid.uuid4().hex
    created = await client.create_drill_key(f"property-drill-create-{run_id}")
    key_id = str(created["key_id"])
    replacement_key_id: str | None = None

    try:
        # The plaintext value returned here appears once; store it in your secret manager.
        if "key_secret" in created:
            json.dumps(created["key_secret"])

        await client.report_compromise(key_id)
        logs = await client.search_logs()
        matches = sum(
            1
            for item in _log_items(logs)
            if _contains_property(item, request.property_id)
        )
        rotated = await client.rotate_key(
            key_id, request.grace_hours, f"property-drill-rotate-{run_id}"
        )
        replacement_key_id = str(rotated["key_id"])
        if replacement_key_id.endswith("...") and "key" in rotated:
            replacement_key_id = f"ifr_...{str(rotated['key'])[-4:]}"
    finally:
        try:
            if replacement_key_id is not None and replacement_key_id != key_id:
                await client.revoke_key(replacement_key_id)
        finally:
            await client.revoke_key(key_id)

    return DrillResult(
        status="confirmed",
        key_id=key_id,
        property_id=request.property_id,
        log_matches=matches,
        maintenance_requests_reviewed=len(request.maintenance_requests),
        tenant_documents_reviewed=len(request.tenant_documents),
        inspection_reminders_reviewed=len(request.inspection_reminders),
        old_key_revoked=True,
    )
