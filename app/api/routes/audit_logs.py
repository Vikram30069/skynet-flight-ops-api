from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.db.models import User, AuditLog, Role
from app.schemas.audit_log import AuditLogResponse
from app.services.permission_service import PermissionService

router = APIRouter()

@router.get("", response_model=list[AuditLogResponse])
def get_audit_logs(
    entity_type: str | None = None,
    entity_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    PermissionService.require_role(current_user, [Role.ADMIN, Role.DISPATCHER, Role.CFI])
    
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
        
    return query.order_by(AuditLog.created_at.desc()).all()
