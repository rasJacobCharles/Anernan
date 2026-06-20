"""
Authentication module handling password operations.
"""

from typing import List

from passlib.context import CryptContext


class Authentication:
    """
    Handles authentication-related operations such as password hashing
    and password verification.
    """

    def __init__(self, schemes: List[str] = None) -> None:
        if schemes is None:
            schemes = ["bcrypt"]
        self.pwd_context = CryptContext(schemes=schemes, deprecated="auto")

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """
        Verify a plain password against its hashed representation.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Generate a bcrypt hash of a plain text password.
        """
        return self.pwd_context.hash(password)
