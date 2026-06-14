"""
Pydantic data schemas for Anernan.
Handles input validation and response serialisation rules.
"""

from typing import List, Optional
import datetime
from pydantic import BaseModel, ConfigDict

# User schemas
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    is_admin: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Document schemas
class DocumentBase(BaseModel):
    filename: str
    file_type: str
    summary: Optional[str] = None
    tags: Optional[List[str]] = None

class DocumentCreate(DocumentBase):
    id: str
    file_path: str
    uploader_id: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: str
    status: str
    uploader_id: Optional[str] = None
    created_at: datetime.datetime
    approved_at: Optional[datetime.datetime] = None
    approved_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentApproval(BaseModel):
    status: str  # 'approved' or 'rejected'
