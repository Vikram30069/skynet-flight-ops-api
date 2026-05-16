from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.db.models import DefectSeverity, DefectStatus

class DefectBase(BaseModel):
    aircraft_id: str
    sortie_id: str | None = None
    severity: DefectSeverity
    description: str

class DefectCreate(DefectBase):
    pass

class DefectResponse(DefectBase):
    id: str
    reported_by: str
    status: DefectStatus
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
