"""
ORM domain initialization.
"""

from .connection import DatabaseConnection
from .management.session import SessionManager, Base
from . import models

# Create default connection and session manager instances
db_connection = DatabaseConnection()
session_manager = SessionManager(db_connection.engine)

# Expose key elements for easy consumption
engine = db_connection.engine
SessionLocal = session_manager.session_factory
get_db = session_manager.get_db

__all__ = [
    "DatabaseConnection",
    "SessionManager",
    "Base",
    "db_connection",
    "session_manager",
    "engine",
    "SessionLocal",
    "get_db",
    "models",
]
