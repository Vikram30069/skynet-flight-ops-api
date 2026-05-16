from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.db.models import SortieStatus

class SortieBase(BaseModel):
    sortie_number: str
    cadet_id: str
    instructor_id: str
    aircraft_id: str
    base_id: str
    lesson_type: str
    scheduled_start: datetime
    scheduled_end: datetime

class SortieCreate(SortieBase):
    pass

class SortieUpdate(BaseModel):
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    delay_minutes: int | None = None
    cancel_reason: str | None = None

class SortieResponse(SortieBase):
    id: str
    status: SortieStatus
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    delay_minutes: int
    cancel_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
