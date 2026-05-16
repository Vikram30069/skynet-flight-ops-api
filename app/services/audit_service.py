from sqlalchemy.orm import Session
from app.db.models import AuditLog, User
import json

class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        actor: User,
        action: str,
        entity_type: str,
        entity_id: str,
        old_value: dict | str | None = None,
        new_value: dict | str | None = None,
        reason: str | None = None
    ):
        if isinstance(old_value, dict):
            old_value = json.dumps(old_value, default=str)
        if isinstance(new_value, dict):
            new_value = json.dumps(new_value, default=str)
            
        log_entry = AuditLog(
            actor_id=actor.id if actor else None,
            actor_role=actor.role.value if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            reason=reason
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
