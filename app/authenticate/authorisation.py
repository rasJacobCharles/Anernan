"""
Authorisation module handling JWT token generation and validation.
"""

import datetime
from typing import Optional

import jwt

# Security configurations
DEFAULT_SECRET_KEY = "super_secret_temporary_key_for_development_purposes"
DEFAULT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60


class Authorisation:
    """
    Handles authorisation-related operations such as JWT token
    generation and validation.
    """

    def __init__(
        self,
        secret_key: str = DEFAULT_SECRET_KEY,
        algorithm: str = DEFAULT_ALGORITHM,
        expire_minutes: int = DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    ) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[datetime.timedelta] = None,
    ) -> str:
        """
        Create a secure JWT access token with a specified expiration time.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta
        else:
            expire = datetime.datetime.utcnow() + datetime.timedelta(
                minutes=self.expire_minutes
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.secret_key, algorithm=self.algorithm
        )
        return encoded_jwt

    def decode_token(self, token: str) -> dict:
        """
        Decode and validate a JWT access token.
        """
        return jwt.decode(
            token, self.secret_key, algorithms=[self.algorithm]
        )
