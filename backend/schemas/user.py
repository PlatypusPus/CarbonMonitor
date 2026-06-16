"""Response schema for user identity."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: str
    facility_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
