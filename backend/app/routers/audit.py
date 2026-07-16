from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/audit", tags=["Audit Engine"])

@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    module: Optional[str] = Query(None, description="Filter by system module"),
    user: Optional[str] = Query(None, description="Filter by user trigger"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (SUCCESS/WARNING/FAILURE)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves a paginated list of audit events.
    Enables searching by module, user, and status fields.
    """
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)

    # Apply filters
    if module:
        query = query.where(AuditLog.module == module.upper())
        count_query = count_query.where(AuditLog.module == module.upper())
    if user:
        query = query.where(AuditLog.user == user.upper())
        count_query = count_query.where(AuditLog.user == user.upper())
    if status_filter:
        query = query.where(AuditLog.status == status_filter.upper())
        count_query = count_query.where(AuditLog.status == status_filter.upper())

    # Order newest first
    query = query.order_by(AuditLog.timestamp.desc())

    # Apply pagination offset
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Execute
    res = await db.execute(query)
    logs = res.scalars().all()

    count_res = await db.execute(count_query)
    total = count_res.scalar() or 0

    return {
        "total": total,
        "logs": logs,
        "page": page,
        "limit": limit
    }

@router.get("/{id}", response_model=AuditLogResponse)
async def get_audit_log_by_id(id: int, db: AsyncSession = Depends(get_db)):
    """Retrieves a single audit event detailed dictionary by its unique database ID."""
    res = await db.execute(select(AuditLog).where(AuditLog.id == id))
    log = res.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit event with ID {id} not found."
        )
        
    return log
