"""
Pydantic data schemas for Token domain.
Handles input validation and response serialisation rules.
"""

from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
