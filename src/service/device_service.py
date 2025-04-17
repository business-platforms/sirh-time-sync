# src/service/device_service.py
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

from zk import ZK, const

from src.domain.models import User, AttendanceRecord, ProcessedStatus
from src.data.repositories import ConfigRepository

logger = logging.getLogger(__name__)


@dataclass
class DeviceConnection:
    """Represents a connection to a ZK device."""
    ip: str
    port: int
    zk: Optional[ZK] = None
    conn = None

    def __post_init__(self):
        self.zk = ZK(self.ip, port=self.port)


class DeviceService:
    """Service for interacting with ZK devices."""

    def __init__(self, config_repository: ConfigRepository):
        self.config_repository = config_repository
        self.connection: Optional[DeviceConnection] = None

    def initialize_connection(self) -> bool:
        """Initialize connection to the device using config."""
        config = self.config_repository.get_config()
        if not config:
            logger.error("No configuration found for device connection")
            return False

        self.connection = DeviceConnection(ip=config.device_ip, port=config.device_port)
        return True

    def connect(self) -> bool:
        """Connect to the ZK device."""
        if not self.connection:
            if not self.initialize_connection():
                return False

        try:
            self.connection.conn = self.connection.zk.connect()
            logger.info(f"Connected to ZK device at {self.connection.ip}:{self.connection.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ZK device: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the ZK device."""
        if self.connection and self.connection.conn:
            self.connection.conn.disconnect()
            logger.info("Disconnected from ZK device")

    def get_users(self) -> List[User]:
        """Get users from the device."""
        if not self.connection or not self.connection.conn:
            if not self.connect():
                logger.error("Not connected to ZK device")
                return []

        try:
            users = self.connection.conn.get_users()
            logger.info(f"Retrieved {len(users)} users")

            return [
                User(
                    user_id=user.user_id,
                    name=user.name,
                )
                for user in users
            ]
        except Exception as e:
            logger.error(f"Error retrieving users: {e}")
            return []

    def set_user(self, user_id: int, code: str) -> bool:
        """Add a user to the device."""
        logger.info("Entering The set_user function to save the user to the device")
        if not self.connection or not self.connection.conn:
            if not self.connect():
                logger.error("Not connected to ZK device")
                return False

        try:
            self.connection.conn.set_user(
                name=code,
                user_id=str(user_id)
            )
            logger.info(f"Added/updated user {code} with ID {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting user: {e}")
            return False

    def get_attendance_records(self) -> List[AttendanceRecord]:
        """Get attendance records from the device."""
        if not self.connection or not self.connection.conn:
            if not self.connect():
                logger.error("Not connected to ZK device")
                return []

        try:
            # First get users to map IDs to names
            users = self.get_users()
            users_map = {user.user_id: user.name for user in users}

            # Get attendance records
            attendance = self.connection.conn.get_attendance()
            processed_records = []

            for record in attendance:
                username = users_map.get(record.user_id, f"Unknown-{record.user_id}")

                processed_record = AttendanceRecord(
                    uid=record.uid,
                    user_id=record.user_id,
                    username=username,
                    timestamp=record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    status=record.status,
                    punch_type=record.punch,
                    processed=ProcessedStatus.UNPROCESSED
                )
                processed_records.append(processed_record)

            logger.info(f"Retrieved {len(processed_records)} attendance records")
            return processed_records
        except Exception as e:
            logger.error(f"Error retrieving attendance data: {e}")
            return []

    def clear_attendance(self) -> bool:
        """Clear attendance records from the device."""
        if not self.connection or not self.connection.conn:
            if not self.connect():
                logger.error("Not connected to ZK device")
                return False

        try:
            self.connection.conn.clear_attendance()
            logger.info("Cleared attendance records from device")
            return True
        except Exception as e:
            logger.error(f"Error clearing attendance data: {e}")
            return False