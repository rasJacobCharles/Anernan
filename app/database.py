"""
Database connection and session initialisation.
Configures SQLite with Write-Ahead Logging (WAL) mode and busy timeout
to optimise concurrent access.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./anernan.db")

# Create the engine with check_same_thread=False for SQLite multithreading compatibility
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Listen to connect event to configure SQLite pragmas
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # Enable WAL mode to allow concurrent reads and handles write queues gracefully
    cursor.execute("PRAGMA journal_mode=WAL;")
    # Set busy timeout (in milliseconds) to resolve potential database lock issues
    cursor.execute("PRAGMA busy_timeout=5000;")
    # Enforce foreign key constraints
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency helper to retrieve a database session and ensure clean closure.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
