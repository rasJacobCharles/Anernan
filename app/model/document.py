"""
Pydantic data schemas for Document domain.
Handles input validation and response serialisation rules.
"""

import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    filename: str
    file_type: str
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    folder: Optional[str] = None


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


class DocumentContentResponse(DocumentResponse):
    content: str


class DocumentApproval(BaseModel):
    status: str  # 'approved' or 'rejected'

