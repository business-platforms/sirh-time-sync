# src/data/database_initializer.py
import sqlite3
import os
import logging
from datetime import datetime

from src.util.paths import get_database_path

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Responsible for initializing the database schema."""

    def __init__(self, db_path=None):
        """Initialize with database path."""
        if db_path is None:
            # Use the persistent database path
            db_path = get_database_path()

        self.db_path = db_path
        logger.info(f"Database initializer configured with path: {db_path}")

    def get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self):
        """Initialize all database tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            logger.info("Starting database initialization")

            # Create config table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY,
                company_id TEXT NOT NULL,
                api_username TEXT NOT NULL,
                api_password TEXT NOT NULL,
                api_secret_key TEXT NOT NULL,
                device_ip TEXT NOT NULL,
                device_port INTEGER NOT NULL,
                collection_interval INTEGER NOT NULL,
                upload_interval INTEGER NOT NULL,
                import_interval INTEGER NOT NULL DEFAULT 12,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Create attendance_records table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY,
                uid INTEGER NOT NULL UNIQUE DEFAULT 2000000,
                user_id INTEGER NOT NULL,
                username TEXT,  
                timestamp TEXT NOT NULL UNIQUE,
                status INTEGER NOT NULL,
                punch_type INTEGER NOT NULL,
                processed TEXT NOT NULL DEFAULT 'UNPROCESSED' 
                    CHECK (processed IN ('PROCESSED', 'ERROR', 'UNPROCESSED')),
                errors TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Create api_upload_logs table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_upload_logs (
                id INTEGER PRIMARY KEY,
                batch_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                records_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                response_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            conn.commit()
            logger.info("Database tables initialized successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error initializing database: {e}")
            raise

        finally:
            conn.close()

    def check_and_upgrade_schema(self):
        """Check if schema needs upgrades and apply them if needed."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Example: Check if we need to add a new column to an existing table
            cursor.execute("PRAGMA table_info(attendance_records)")
            columns = [column[1] for column in cursor.fetchall()]

            # Add any missing columns or make other schema changes
            if 'errors' not in columns:
                logger.info("Upgrading schema: Adding 'errors' column to attendance_records")
                cursor.execute("ALTER TABLE attendance_records ADD COLUMN errors TEXT")

            conn.commit()
            logger.info("Database schema checked and upgraded if needed")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error checking/upgrading database schema: {e}")
            raise

        finally:
            conn.close()

    def run_initialization(self):
        """Run full database initialization process."""
        try:
            self.initialize_database()
            self.check_and_upgrade_schema()
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False