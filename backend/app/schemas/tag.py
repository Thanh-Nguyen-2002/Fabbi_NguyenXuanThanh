import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class TagBase(BaseModel):
    name: str = Field(..., max_length=50)
    color: Optional[str] = Field(default="#000000", max_length=20)

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)

class TagResponse(TagBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
