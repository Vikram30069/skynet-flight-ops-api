from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.db.models import TrainingProgressStatus

class TrainingProgressBase(BaseModel):
    sortie_id: str
    lesson_type: str
    maneuver_score: int | None = Field(None, ge=1, le=5)
    communication_score: int | None = Field(None, ge=1, le=5)
    situational_awareness_score: int | None = Field(None, ge=1, le=5)
    remarks: str | None = None

class TrainingProgressCreate(TrainingProgressBase):
    pass

class TrainingProgressUpdate(BaseModel):
    maneuver_score: int | None = Field(None, ge=1, le=5)
    communication_score: int | None = Field(None, ge=1, le=5)
    situational_awareness_score: int | None = Field(None, ge=1, le=5)
    remarks: str | None = None

class TrainingProgressReject(BaseModel):
    rejection_reason: str

class TrainingProgressResponse(TrainingProgressBase):
    id: str
    cadet_id: str
    instructor_id: str
    status: TrainingProgressStatus
    submitted_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
