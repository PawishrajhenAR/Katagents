import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.analytics import AuditLog


async def log_audit(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    ip: str | None = None,
    metadata: dict | None = None,
) -> None:
    entry = AuditLog(
        org_id=org_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip=ip,
        metadata_json=metadata or {},
    )
    db.add(entry)
