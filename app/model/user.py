"""
Pydantic data schemas for User domain.
Handles input validation and response serialisation rules.
"""

import datetime
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    is_admin: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
