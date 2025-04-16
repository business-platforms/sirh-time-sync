# src/data/repository_base.py
import os
import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SQLiteRepositoryBase:
    """Base class for SQLite repositories with auto-initialization."""

    _db_initialized = False  # Class variable to track initialization

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, 'data', 'attendance.db')

            # Ensure data directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path

        # Initialize database if not already done
        if not SQLiteRepositoryBase._db_initialized:
            self._initialize_database()
            SQLiteRepositoryBase._db_initialized = True

    def get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_database(self):
        """Initialize database tables if they don't exist."""
        from src.data.database_initializer import DatabaseInitializer
        initializer = DatabaseInitializer(self.db_path)
        initializer.run_initialization()
        logger.info("Database initialized automatically")