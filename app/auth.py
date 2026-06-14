"""
Authentication and authorisation utilities for Anernan.
Handles password hashing via bcrypt and JWT token generation/validation.
"""

import datetime
from typing import Optional
import jwt
from passlib.context import CryptContext

# CryptContext configured to use bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security configuration (typically loaded from environment variables in production)
SECRET_KEY = "super_secret_temporary_key_for_development_purposes"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hashed representation.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Generate a bcrypt hash of a plain text password.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    Create a secure JWT access token with a specified expiration time.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
