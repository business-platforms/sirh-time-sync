# src/data/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.models import AttendanceRecord, User, Config, APIUploadLog, ProcessedStatus


class ConfigRepository(ABC):
    """Interface for config data access."""

    @abstractmethod
    def get_config(self) -> Optional[Config]:
        """Get the system configuration."""
        pass

    @abstractmethod
    def save_config(self, config: Config) -> None:
        """Save the system configuration."""
        pass


class AttendanceRepository(ABC):
    """Interface for attendance record data access."""

    @abstractmethod
    def get_records(self, processed_status: Optional[str] = None, order_by: str = 'timestamp') -> List[
        AttendanceRecord]:
        """Get attendance records with optional filtering."""
        pass

    @abstractmethod
    def save_record(self, record: AttendanceRecord) -> AttendanceRecord:
        """Save an attendance record."""
        pass

    @abstractmethod
    def save_records(self, records: List[AttendanceRecord]) -> None:
        """Save multiple attendance records."""
        pass

    @abstractmethod
    def update_record(self, record: AttendanceRecord) -> None:
        """Update an attendance record."""
        pass

    @abstractmethod
    def delete_record(self, record_id: int) -> None:
        """Delete an attendance record."""
        pass

    @abstractmethod
    def delete_records(self, ids: List[int]) -> None:
        """Delete a list of records"""
        pass

    @abstractmethod
    def mark_records_by_timestamps(self, timestamps: List[str], status: str = ProcessedStatus.PROCESSED) -> None:
        """Mark records as processed by their timestamps."""
        pass

    @abstractmethod
    def mark_records_by_ids(self, ids: List[int], status: str = ProcessedStatus.PROCESSED) -> None:
        """Mark records as processed by ids."""
        pass

    @abstractmethod
    def mark_record_error(self, record_id: int, errors: List[Dict[str, str]]) -> None:
        """Mark a record as having errors."""
        pass


class UserRepository(ABC):
    """Interface for user data access."""

    @abstractmethod
    def get_users(self) -> List[User]:
        """Get all users."""
        pass

    @abstractmethod
    def save_user(self, user: User) -> User:
        """Save a user."""
        pass

    @abstractmethod
    def update_user(self, user: User) -> None:
        """Update a user."""
        pass

    @abstractmethod
    def delete_user(self, user_id: int) -> None:
        """Delete a user."""
        pass


class LogRepository(ABC):
    """Interface for log data access."""

    @abstractmethod
    def log_api_upload(self, log: APIUploadLog) -> None:
        """Log an API upload."""
        pass

    @abstractmethod
    def get_api_logs(self, limit: int = 100) -> List[APIUploadLog]:
        """Get recent API upload logs."""
        pass