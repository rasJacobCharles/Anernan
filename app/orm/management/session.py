"""
Database session management and lifecycle.
"""

from typing import Generator

from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.engine import Engine

Base = declarative_base()


class SessionManager:
    """
    Handles database session creation and lifecycle helpers.
    """

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def get_session(self) -> Session:
        """
        Create and return a new database session.
        """
        return self.session_factory()

    def get_db(self) -> Generator[Session, None, None]:
        """
        Dependency helper to retrieve a database session and ensure clean closure.
        """
        db = self.get_session()
        try:
            yield db
        finally:
            db.close()
