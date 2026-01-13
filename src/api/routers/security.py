"""Security, roles, and audit endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import schemas
from ..store import fake_db


router = APIRouter(prefix="", tags=["Security"])


@router.get("/audit/logs", response_model=list[schemas.AuditLogResponse])
def list_audit_logs() -> list[schemas.AuditLogResponse]:
    return [schemas.AuditLogResponse(**log) for log in fake_db.audit_logs]


@router.post("/audit/search", response_model=list[schemas.AuditLogResponse])
def search_audit_logs(payload: schemas.AuditSearchRequest) -> list[schemas.AuditLogResponse]:
    results = []
    for log in fake_db.audit_logs:
        if payload.action and log["action"] != payload.action:
            continue
        if payload.date_from and log["timestamp"] < payload.date_from:
            continue
        if payload.date_to and log["timestamp"] > payload.date_to:
            continue
        results.append(log)
    return [schemas.AuditLogResponse(**log) for log in results]


@router.get("/roles", response_model=list[schemas.RoleResponse])
def list_roles() -> list[schemas.RoleResponse]:
    return [
        schemas.RoleResponse(id=role_id, name=role_data["name"], permissions=role_data["permissions"])
        for role_id, role_data in fake_db.roles.items()
    ]


@router.put("/roles/{role_id}", response_model=schemas.RoleResponse)
def update_role(role_id: str, payload: schemas.RolePermissionsUpdate) -> schemas.RoleResponse:
    if role_id not in fake_db.roles:
        raise HTTPException(status_code=404, detail="Role not found")
    fake_db.roles[role_id]["permissions"] = payload.permissions
    fake_db._log("role_update", f"Role {role_id} updated")
    role = fake_db.roles[role_id]
    return schemas.RoleResponse(id=role_id, name=role["name"], permissions=role["permissions"])
