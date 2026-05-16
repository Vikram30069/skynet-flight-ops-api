from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: str
    actor_id: str | None
    actor_role: str | None
    action: str
    entity_type: str
    entity_id: str
    old_value: str | None
    new_value: str | None
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
