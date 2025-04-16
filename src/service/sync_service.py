# src/service/sync_service.py
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from src.service.api_service import APIService
from src.service.attendance_service import AttendanceService
from src.service.device_service import DeviceService
from src.domain.models import User, ProcessedStatus

logger = logging.getLogger(__name__)


class SyncService:
    """Service for synchronizing data between the device and API."""

    def __init__(
            self,
            api_service: APIService,
            attendance_service: AttendanceService,
            device_service: DeviceService
    ):
        self.api_service = api_service
        self.attendance_service = attendance_service
        self.device_service = device_service

    def import_users_from_api_to_device(self) -> int:
        """Import users from API to the device."""
        try:
            # Get employees from API
            employees = self.api_service.get_employees()
            if not employees:
                logger.warning("No employees found from API")
                return 0

            # Get existing users from device
            device_users = self.device_service.get_users()
            saved_codes = {user.name for user in device_users}

            # Add new users to device
            imported = 0
            for employee in employees:
                emp_id = employee.get('id')
                code = employee.get('code')

                if not emp_id or not code:
                    logger.warning(f"Skipping employee due to missing data: {employee}")
                    continue

                if code in saved_codes:
                    logger.debug(f"Skipping employee: {employee}, already saved")
                    continue

                if self.device_service.set_user(emp_id, code):
                    imported += 1

            logger.info(f"Imported {imported} users from API to device")
            return imported

        except Exception as e:
            logger.error(f"Error importing users from API to device: {e}")
            return 0

    def upload_attendance_to_api(self) -> Dict[str, Any]:
        """Upload attendance records to API."""
        try:
            # Get unprocessed records
            records = self.attendance_service.get_unprocessed_records()
            if not records:
                logger.info("No unprocessed attendance records to upload")
                return {'success': True, 'message': 'No records to upload', 'processed': 0}

            # Create Excel report
            export_info = self.attendance_service.create_excel_report(records)
            if not export_info:
                logger.warning("Failed to create Excel report")
                return {'success': False, 'message': 'Failed to create Excel report', 'processed': 0}

            # Upload to API
            response = self.api_service.upload_attendance(export_info['file_path'])

            if not response.get('success', False):
                # Log failed upload
                self.attendance_service.log_api_upload({
                    'batch_id': export_info['batch_id'],
                    'file_path': export_info['file_path'],
                    'records_count': export_info['records_count'],
                    'status': 'FAILED',
                    'response_data': response
                })

                logger.error(f"Failed to upload attendance records: {response.get('message', 'Unknown error')}")
                return {'success': False, 'message': response.get('message', 'Unknown error'), 'processed': 0}

            # Process the job execution
            job_execution_id = response.get('jobExecutionId')
            processed_count = self._process_upload_job(job_execution_id, records, export_info)

            return {
                'success': True,
                'message': f'Successfully processed {processed_count} records',
                'processed': processed_count,
                'jobExecutionId': job_execution_id
            }

        except Exception as e:
            logger.error(f"Error uploading attendance to API: {e}")
            return {'success': False, 'message': str(e), 'processed': 0}

    def _process_upload_job(self, job_execution_id: str, records: List[Any], export_info: Dict[str, Any]) -> int:
        """Process the upload job and update record statuses."""
        try:
            # Wait for job completion with timeout
            end_time = datetime.now() + timedelta(seconds=30)
            processed_count = 0

            while datetime.now() < end_time:
                # Check job status
                pointing_import = self.api_service.get_pointing_import()
                import_status = pointing_import.get('status')

                if import_status == "COMPLETED":
                    logger.info("Pointing import completed successfully")

                    # Get processed pointings
                    job_id = pointing_import.get('jobExecutionId', job_execution_id)
                    attendance_records = self.api_service.get_pointings_with_job_id(job_id)

                    if attendance_records:
                        # Mark records as processed
                        self.attendance_service.mark_records_processed_by_timestamps(attendance_records)
                        processed_count = len(attendance_records)

                    # Check for errors
                    if len(attendance_records) != len(records):
                        self._process_error_records()

                    # Log successful upload
                    self.attendance_service.log_api_upload({
                        'batch_id': export_info['batch_id'],
                        'file_path': export_info['file_path'],
                        'records_count': export_info['records_count'],
                        'status': 'SUCCESS',
                        'response_data': {
                            'jobExecutionId': job_id,
                            'processed': processed_count
                        }
                    })

                    return processed_count

                elif import_status in ["STARTED", "STARTING"]:
                    logger.debug("Pointing import still in progress")
                    time.sleep(2)

                elif import_status in ["FAILED", "STOPPED"]:
                    logger.error("Pointing import failed")

                    # Log failure
                    self.attendance_service.log_api_upload({
                        'batch_id': export_info['batch_id'],
                        'file_path': export_info['file_path'],
                        'records_count': export_info['records_count'],
                        'status': 'FAILED',
                        'response_data': pointing_import
                    })

                    self._process_error_records()
                    return 0

                else:
                    logger.warning(f"Unknown import status: {import_status}")
                    time.sleep(2)

            # Timeout reached
            logger.warning("Timeout reached waiting for pointing import to complete")
            return 0

        except Exception as e:
            logger.error(f"Error processing upload job: {e}")
            return 0

    def _process_error_records(self) -> None:
        """Process error records from the API."""
        try:
            failed_records = self.api_service.get_pointing_import_lines()

            for failed_record in failed_records:
                record_id = failed_record.get("recordId")
                errors = failed_record.get("errors", [])

                if record_id and errors:
                    self.attendance_service.mark_record_error(record_id, errors)

        except Exception as e:
            logger.error(f"Error processing failed records: {e}")