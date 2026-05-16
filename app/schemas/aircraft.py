from pydantic import BaseModel
from datetime import datetime
from app.db.models import AircraftStatus

class AircraftBase(BaseModel):
    registration: str
    aircraft_type: str
    base_id: str
    tbo_remaining_hours: int = 2000

class AircraftCreate(AircraftBase):
    pass

class AircraftResponse(AircraftBase):
    id: str
    status: AircraftStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
