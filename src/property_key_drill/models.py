from typing import Literal

from pydantic import BaseModel, Field


class MaintenanceRequest(BaseModel):
    request_id: str
    property_id: str
    summary: str


class TenantDocument(BaseModel):
    document_id: str
    property_id: str
    kind: Literal["lease", "insurance", "identity"]


class InspectionReminder(BaseModel):
    reminder_id: str
    property_id: str
    due_on: str


class DrillRequest(BaseModel):
    property_id: str
    maintenance_requests: list[MaintenanceRequest] = Field(default_factory=list)
    tenant_documents: list[TenantDocument] = Field(default_factory=list)
    inspection_reminders: list[InspectionReminder] = Field(default_factory=list)
    grace_hours: int = Field(default=1, ge=0, le=24)


class DrillResult(BaseModel):
    status: Literal["confirmed"]
    key_id: str
    property_id: str
    log_matches: int
    maintenance_requests_reviewed: int
    tenant_documents_reviewed: int
    inspection_reminders_reviewed: int
    old_key_revoked: bool
