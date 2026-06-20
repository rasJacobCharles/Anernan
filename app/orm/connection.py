"""
Database connection configuration and engine setup for the ORM domain.
"""

import os

from sqlalchemy import create_engine, event, Engine


class DatabaseConnection:
    """
    Handles database connection setup, engine creation, and SQLite configuration.
    """

    def __init__(self, database_url: str = None) -> None:
        self.database_url = database_url or os.environ.get(
            "DATABASE_URL", "sqlite:///./database/anernan.db"
        )
        self._ensure_directory()
        self.engine = self._create_engine()
        self._configure_sqlite()

    def _ensure_directory(self) -> None:
        """
        Ensure the database directory exists if using SQLite.
        """
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.split("sqlite:///", 1)[1]
            if db_path and db_path != ":memory:":
                db_dir = os.path.dirname(db_path)
                if db_dir:
                    os.makedirs(db_dir, exist_ok=True)

    def _create_engine(self) -> Engine:
        """
        Create the SQLAlchemy engine.
        """
        connect_args = {}
        if self.database_url.startswith("sqlite"):
            # Required for SQLite multithreading compatibility
            connect_args["check_same_thread"] = False
        return create_engine(self.database_url, connect_args=connect_args)

    def _configure_sqlite(self) -> None:
        """
        Configure SQLite pragmas (WAL mode, busy timeout, foreign keys).
        """
        if not self.database_url.startswith("sqlite"):
            return

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            # Enable WAL mode to allow concurrent reads and handle write queues
            cursor.execute("PRAGMA journal_mode=WAL;")
            # Set busy timeout (in milliseconds) to resolve database lock issues
            cursor.execute("PRAGMA busy_timeout=5000;")
            # Enforce foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()
