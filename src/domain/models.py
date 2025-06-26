from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class ProcessedStatus(str, Enum):
    PROCESSED = "PROCESSED"
    ERROR = "ERROR"
    UNPROCESSED = "UNPROCESSED"


class PunchType(int, Enum):
    IN = 0
    OUT = 1

    @classmethod
    def to_string(cls, value: int) -> str:
        return "entree" if value == cls.IN else "sortie"


@dataclass
class User:
    """User entity representing an employee."""
    id: Optional[int] = None
    user_id: int = 0
    name: str = ""
    code: str = ""
    created_at: Optional[datetime] = None

    @property
    def display_name(self) -> str:
        """Return a display name for the user."""
        return f"{self.name} ({self.code})" if self.name and self.code else self.name or self.code


@dataclass
class AttendanceRecord:
    """Attendance record entity."""
    id: Optional[int] = None
    uid: Optional[int] = None
    user_id: int = 0
    username: str = ""
    timestamp: str = ""
    status: int = 0
    punch_type: int = 0
    processed: str = ProcessedStatus.UNPROCESSED
    errors: List[Dict[str, str]] = field(default_factory=list)
    created_at: Optional[datetime] = None

    def mark_as_processed(self) -> None:
        """Mark the record as processed."""
        self.processed = ProcessedStatus.PROCESSED
        self.errors = []

    def mark_as_error(self, error_code: str, field: str, message: str) -> None:
        """Mark the record as having an error."""
        self.processed = ProcessedStatus.ERROR
        self.errors.append({
            "field": field,
            "code": error_code,
            "message": message
        })

    def mark_as_unprocessed(self) -> None:
        """Mark the record as unprocessed."""
        self.processed = ProcessedStatus.UNPROCESSED
        self.errors = []

    def is_processed(self) -> bool:
        """Check if the record is processed."""
        return self.processed == ProcessedStatus.PROCESSED

    def has_errors(self) -> bool:
        """Check if the record has errors."""
        return self.processed == ProcessedStatus.ERROR and len(self.errors) > 0


@dataclass
class Config:
    """System configuration entity."""
    id: Optional[int] = None
    company_id: str = ""
    api_username: str = ""
    api_password: str = ""
    api_secret_key: str = ""
    device_ip: str = ""
    device_port: int = 4370
    collection_interval: int = 60
    upload_interval: int = 1
    import_interval: int = 12
    automatic_detection: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class APIUploadLog:
    """Log of API uploads."""
    id: Optional[int] = None
    batch_id: str = ""
    file_path: str = ""
    records_count: int = 0
    status: str = ""
    response_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None