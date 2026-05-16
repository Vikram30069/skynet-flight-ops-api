from pydantic import BaseModel
from datetime import datetime

class BaseEntityBase(BaseModel):
    name: str
    code: str
    location: str | None = None

class BaseEntityCreate(BaseEntityBase):
    pass

class BaseEntityResponse(BaseEntityBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
