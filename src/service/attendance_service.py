# src/service/attendance_service.py
import logging
import os
import uuid
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

from src.domain.models import AttendanceRecord, APIUploadLog, ProcessedStatus, PunchType
from src.data.repositories import AttendanceRepository, LogRepository
from src.service.device_service import DeviceService

logger = logging.getLogger(__name__)


class AttendanceService:
    """Service for managing attendance records."""

    def __init__(
            self,
            attendance_repository: AttendanceRepository,
            log_repository: LogRepository,
            device_service: DeviceService
    ):
        self.attendance_repository = attendance_repository
        self.log_repository = log_repository
        self.device_service = device_service

        # Ensure exports directory exists
        os.makedirs('exports', exist_ok=True)

    def collect_attendance(self) -> int:
        """Collect attendance data from device and save to database."""
        try:
            # Get records from device
            records = self.device_service.get_attendance_records()
            if not records:
                logger.info("No attendance records to collect")
                return 0

            # Save records to database
            self.attendance_repository.save_records(records)
            logger.info(f"Collected and saved {len(records)} attendance records")

            return len(records)
        except Exception as e:
            logger.error(f"Error collecting attendance: {e}")
            return 0

    def get_unprocessed_records(self) -> List[AttendanceRecord]:
        """Get unprocessed attendance records."""
        return self.attendance_repository.get_records(processed_status=ProcessedStatus.UNPROCESSED)

    def get_records_by_status(self, status: Optional[str] = None) -> List[AttendanceRecord]:
        """Get attendance records by status."""
        return self.attendance_repository.get_records(processed_status=status)

    def create_excel_report(self, records: List[AttendanceRecord]) -> Optional[Dict[str, Any]]:
        """Create an Excel report from attendance records."""
        if not records:
            logger.info("No records to export")
            return None

        try:
            # Create a unique filename
            batch_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"exports/attendance_{timestamp}_{batch_id}.xlsx"

            # Create a DataFrame for export
            export_data = [
                {
                    'code': record.username,
                    'Nom': None,
                    'time': record.timestamp,
                    'type': PunchType.to_string(record.punch_type),
                    'recordId': record.id
                }
                for record in records
            ]

            if not export_data:
                logger.warning("No valid records to export")
                return None

            # Create DataFrame and export to Excel
            export_df = pd.DataFrame(export_data)
            export_df.to_excel(filename, index=False)

            logger.info(f"Created Excel report with {len(records)} records at {filename}")

            return {
                'batch_id': batch_id,
                'file_path': filename,
                'records_count': len(records)
            }
        except Exception as e:
            logger.error(f"Error creating Excel report: {e}")
            return None

    def mark_record_processed(self, record_id: int) -> bool:
        """Mark a record as processed."""
        try:
            records = self.attendance_repository.get_records()
            record = next((r for r in records if r.id == record_id), None)

            if not record:
                logger.error(f"Record with ID {record_id} not found")
                return False

            record.processed = ProcessedStatus.PROCESSED
            record.errors = []

            self.attendance_repository.update_record(record)
            logger.info(f"Marked record {record_id} as processed")
            return True
        except Exception as e:
            logger.error(f"Error marking record as processed: {e}")
            return False

    def mark_record_error(self, record_id: int, errors: List[Dict[str, str]]) -> bool:
        """Mark a record as having errors."""
        try:
            self.attendance_repository.mark_record_error(record_id, errors)
            return True
        except Exception as e:
            logger.error(f"Error marking record error: {e}")
            return False

    def mark_records_processed_by_timestamps(self, timestamps: List[str]) -> bool:
        """Mark records as processed by their timestamps."""
        try:
            self.attendance_repository.mark_records_by_timestamps(timestamps, ProcessedStatus.PROCESSED)
            return True
        except Exception as e:
            logger.error(f"Error marking records as processed: {e}")
            return False

    def log_api_upload(self, log_data: Dict[str, Any]) -> None:
        """Log an API upload attempt."""
        try:
            log = APIUploadLog(
                batch_id=log_data.get('batch_id', ''),
                file_path=log_data.get('file_path', ''),
                records_count=log_data.get('records_count', 0),
                status=log_data.get('status', ''),
                response_data=log_data.get('response_data')
            )
            self.log_repository.log_api_upload(log)
        except Exception as e:
            logger.error(f"Error logging API upload: {e}")