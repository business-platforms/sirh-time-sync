# src/data/sqlite_repositories.py
import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.data.repository_base import SQLiteRepositoryBase
from src.domain.models import AttendanceRecord, User, Config, APIUploadLog, ProcessedStatus
from src.data.repositories import ConfigRepository, AttendanceRepository, UserRepository, LogRepository

logger = logging.getLogger(__name__)


class SQLiteRepository:
    """Base class for SQLite repositories."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, 'data', 'attendance.db')
        self.db_path = db_path

    def get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


class SQLiteConfigRepository(SQLiteRepositoryBase, ConfigRepository):
    """SQLite implementation of ConfigRepository."""

    def get_config(self) -> Optional[Config]:
        """Get the system configuration from the database."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM config LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            return Config(
                id=row['id'],
                company_id=row['company_id'],
                api_username=row['api_username'],
                api_password=row['api_password'],
                device_ip=row['device_ip'],
                device_port=row['device_port'],
                collection_interval=row['collection_interval'],
                upload_interval=row['upload_interval'],
                import_interval=row['import_interval'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        return None

    def save_config(self, config: Config) -> None:
        """Save the system configuration to the database."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM config LIMIT 1")
        existing_config = cursor.fetchone()

        now = datetime.now()

        if existing_config:
            cursor.execute('''
            UPDATE config SET 
                company_id = ?, api_username = ?, api_password = ?, 
                device_ip = ?, device_port = ?, collection_interval = ?, 
                upload_interval = ?, import_interval = ?, updated_at = ? 
            WHERE id = ?
            ''', (
                config.company_id, config.api_username, config.api_password,
                config.device_ip, config.device_port, config.collection_interval,
                config.upload_interval, config.import_interval, now, existing_config['id']
            ))
        else:
            cursor.execute('''
            INSERT INTO config (
                company_id, api_username, api_password, device_ip, device_port, 
                collection_interval, upload_interval, import_interval, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                config.company_id, config.api_username, config.api_password,
                config.device_ip, config.device_port, config.collection_interval,
                config.upload_interval, config.import_interval, now, now
            ))

        conn.commit()
        conn.close()
        logger.info("Config saved successfully")


class SQLiteAttendanceRepository(SQLiteRepositoryBase, AttendanceRepository):
    """SQLite implementation of AttendanceRepository."""

    def get_records(self, processed_status: Optional[str] = None, order_by: str = 'timestamp') -> List[
        AttendanceRecord]:
        """Get attendance records with optional filtering."""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM attendance_records'
        params = []

        if processed_status is not None:
            query += ' WHERE processed = ?'
            params.append(processed_status)

        query += f' ORDER BY {order_by} ASC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            AttendanceRecord(
                id=row['id'],
                uid=row['uid'],
                user_id=row['user_id'],
                username=row['username'],
                timestamp=row['timestamp'],
                status=row['status'],
                punch_type=row['punch_type'],
                processed=row['processed'],
                errors=json.loads(row['errors']) if row['errors'] else [],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]

    def save_record(self, record: AttendanceRecord) -> AttendanceRecord:
        """Save an attendance record."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Get next UID if not provided
            if not record.uid:
                cursor.execute('SELECT MAX(uid) FROM attendance_records')
                max_uid = cursor.fetchone()[0]
                record.uid = max_uid + 1 if max_uid and max_uid >= 2000000 else 2000000

            errors_json = json.dumps(record.errors) if record.errors else None

            cursor.execute('''
                INSERT INTO attendance_records (
                    uid, user_id, username, timestamp, status, punch_type, processed, errors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.uid, record.user_id, record.username, record.timestamp,
                record.status, record.punch_type, record.processed, errors_json
            ))

            # Get the inserted record's ID
            record.id = cursor.lastrowid

            conn.commit()
            logger.info(f"Saved attendance record with id {record.id} to database")
            return record
        finally:
            conn.close()

    def save_records(self, records: List[AttendanceRecord]) -> None:
        """Save multiple attendance records."""
        if not records:
            return

        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Start with the maximum UID in the database
            cursor.execute('SELECT MAX(uid) FROM attendance_records')
            max_uid = cursor.fetchone()[0]
            next_uid = max_uid + 1 if max_uid and max_uid > 2000000 else 2000000

            for record in records:
                if not record.uid:
                    record.uid = next_uid
                    next_uid += 1

                errors_json = json.dumps(record.errors) if record.errors else None

                cursor.execute('''
                    INSERT OR IGNORE INTO attendance_records (
                        uid, user_id, username, timestamp, status, punch_type, processed, errors
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.uid, record.user_id, record.username, record.timestamp,
                    record.status, record.punch_type, record.processed, errors_json
                ))

            conn.commit()
            logger.info(f"Saved {len(records)} attendance records to database")
        finally:
            conn.close()

    def update_record(self, record: AttendanceRecord) -> None:
        """Update an attendance record."""
        if not record.id:
            raise ValueError("Record ID is required for update")

        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            errors_json = json.dumps(record.errors) if record.errors else None

            cursor.execute('''
                UPDATE attendance_records
                SET 
                    username = ?,
                    timestamp = ?,
                    status = ?,
                    punch_type = ?,
                    processed = ?,
                    errors = ?
                WHERE id = ?
            ''', (
                record.username,
                record.timestamp,
                record.status,
                record.punch_type,
                record.processed,
                errors_json,
                record.id
            ))

            conn.commit()
            logger.info(f"Updated attendance record with id {record.id}")
        finally:
            conn.close()

    def delete_record(self, record_id: int) -> None:
        """Delete an attendance record."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM attendance_records WHERE id = ?', (record_id,))
            conn.commit()
            logger.info(f"Deleted attendance record with id {record_id}")
        finally:
            conn.close()

    def delete_records(self, ids: List[int]) -> None:
        """Delete a list of records"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            placeholders = ', '.join('?' * len(ids))
            query = f'DELETE FROM attendance_records WHERE id IN ({placeholders})'
            cursor.execute(query, ids)
            conn.commit()
            logger.info(f"Deleted attendance records with ids {ids}")
        finally:
            conn.close()

    def mark_records_by_timestamps(self, timestamps: List[str], status: str = ProcessedStatus.PROCESSED) -> None:
        """Mark records as processed by their timestamps."""
        if not timestamps:
            return

        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            placeholders = ','.join(['?'] * len(timestamps))
            formatted_timestamps = [ts.replace("T", " ") for ts in timestamps]

            cursor.execute(f'''
                UPDATE attendance_records 
                SET processed = ?, errors = NULL
                WHERE timestamp IN ({placeholders})
            ''', [status] + formatted_timestamps)

            conn.commit()
            logger.info(f"Marked {len(timestamps)} records as {status}")
        finally:
            conn.close()

    def mark_record_error(self, record_id: int, errors: List[Dict[str, str]]) -> None:
        """Mark a record as having errors."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            errors_json = json.dumps(errors) if errors else None

            cursor.execute('''
                UPDATE attendance_records 
                SET processed = ?, errors = ?
                WHERE id = ?
            ''', (ProcessedStatus.ERROR, errors_json, record_id))

            conn.commit()
            logger.info(f"Marked record {record_id} as ERROR with {len(errors)} errors")
        finally:
            conn.close()


class SQLiteLogRepository(SQLiteRepositoryBase, LogRepository):
    """SQLite implementation of LogRepository."""

    def log_api_upload(self, log: APIUploadLog) -> None:
        """Log an API upload."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            response_json = json.dumps(log.response_data) if log.response_data else None

            cursor.execute('''
            INSERT INTO api_upload_logs (
                batch_id, file_path, records_count, status, response_data
            ) VALUES (?, ?, ?, ?, ?)
            ''', (
                log.batch_id, log.file_path, log.records_count, log.status, response_json
            ))

            conn.commit()
            logger.info(f"Logged API upload: {log.batch_id}, {log.status}")
        finally:
            conn.close()

    def get_api_logs(self, limit: int = 100) -> List[APIUploadLog]:
        """Get recent API upload logs."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM api_upload_logs ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [
            APIUploadLog(
                id=row['id'],
                batch_id=row['batch_id'],
                file_path=row['file_path'],
                records_count=row['records_count'],
                status=row['status'],
                response_data=json.loads(row['response_data']) if row['response_data'] else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]