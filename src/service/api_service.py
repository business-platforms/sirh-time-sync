# src/service/api_service.py
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import requests

from src.data.repositories import ConfigRepository
from src.domain.models import User

logger = logging.getLogger(__name__)


class APIService:
    """Service for interacting with the RHP SaaS API."""

    def __init__(self, config_repository: ConfigRepository, api_url: str):
        self.config_repository = config_repository
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        self.xsrf_token = None
        self.jwt_token = None
        self._company_id = None
        self._username = None
        self._password = None

    def initialize(self) -> bool:
        """Initialize the API client with configuration."""
        config = self.config_repository.get_config()
        if not config:
            logger.error("No configuration found for API service")
            return False

        self._company_id = config.company_id
        self._username = config.api_username
        self._password = config.api_password

        return True

    def authenticate(self) -> bool:
        """Authenticate with the API using XSRF and JWT."""
        if not self._company_id or not self._username or not self._password:
            if not self.initialize():
                return False

        try:
            # Step 1: Get XSRF token
            response = self.session.get(f"{self.api_url}/auth/hello")
            if response.status_code != 200:
                logger.error(f"Failed to get XSRF token: {response.status_code}")
                return False

            # Extract XSRF token from cookies
            if 'XSRF-TOKEN' in self.session.cookies:
                self.xsrf_token = self.session.cookies['XSRF-TOKEN']
                logger.debug("Successfully obtained XSRF token")
            else:
                logger.error("XSRF token not found in response cookies")
                return False

            # Step 2: Perform login to get JWT token
            headers = {
                'X-XSRF-TOKEN': self.xsrf_token,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            data = {
                'username': self._username,
                'password': self._password,
                'company_id': self._company_id
            }

            response = self.session.post(
                f"{self.api_url}/auth/login",
                json=data,
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"Authentication failed: {response.status_code}")
                logger.debug(f"Response: {response.text}")
                return False

            # Extract JWT token from response
            auth_data = response.json()

            # After login, update token
            if 'XSRF-TOKEN' in self.session.cookies:
                self.xsrf_token = self.session.cookies['XSRF-TOKEN']

            if 'access_token' in auth_data:
                self.jwt_token = auth_data['access_token']
                logger.info("Successfully authenticated with API")
                return True
            else:
                logger.error("JWT token not found in authentication response")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication tokens."""
        if not self.jwt_token or not self.xsrf_token:
            if not self.authenticate():
                raise Exception("Authentication required")

        return {
            'X-XSRF-TOKEN': self.xsrf_token,
            'Authorization': f"Bearer {self.jwt_token}",
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def upload_attendance(self, file_path: str) -> Dict[str, Any]:
        """Upload attendance data from an Excel file to the API."""
        if not self.initialize():
            return {'success': False, 'message': 'Failed to initialize API service'}

        try:
            headers = self.get_auth_headers()
            # Remove Content-Type as it will be set by requests for multipart/form-data
            headers.pop('Content-Type', None)

            with open(file_path, 'rb') as file:
                files = {
                    'file': (file_path.split('/')[-1], file,
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                }

                month = datetime.now().strftime("%Y-%m")
                response = self.session.post(
                    f"{self.api_url}/pay/api/companies/{self._company_id}/month-pointing/{month}/import",
                    headers=headers,
                    files=files
                )

            if response.status_code == 200:
                response_data = response.json()
                job_execution_id = response_data.get("jobExecutionId")
                logger.info(f"Job execution started with ID: {job_execution_id}")
                return {'success': True, 'jobExecutionId': job_execution_id}
            elif response.status_code == 401:
                # Token might be expired, try to re-authenticate
                logger.warning("Authentication token expired, attempting to re-authenticate")
                if self.authenticate():
                    # Retry with new token
                    return self.upload_attendance(file_path)
                else:
                    return {'success': False, 'message': 'Re-authentication failed'}
            else:
                logger.error(f"API upload failed: {response.status_code}")
                logger.debug(f"Response: {response.text}")
                return {'success': False, 'message': f'API Error: {response.text}'}

        except Exception as e:
            logger.error(f"Error uploading attendance data: {e}")
            return {'success': False, 'message': str(e)}

    def get_employees(self) -> List[Dict[str, Any]]:
        """Get employee data from the API."""
        if not self._company_id:
            if not self.initialize():
                return []

        try:
            headers = self.get_auth_headers()
            response = self.session.get(
                f"{self.api_url}/companymanagement/api/companies/{self._company_id}/employees/minimal?includeInactive=false",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get employees: {response.status_code}")
                logger.debug(f"Response: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error getting employees: {e}")
            return []

    def get_pointing_import(self) -> Dict[str, Any]:
        """Get pointing import status."""
        if not self._company_id:
            if not self.initialize():
                return {}

        try:
            headers = self.get_auth_headers()

            response = self.session.get(
                f"{self.api_url}/pay/api/companies/{self._company_id}/pointing-imports",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                logger.info("Pointing import data retrieved successfully.")
                return {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "companyId": data.get("companyId"),
                    "jobExecutionId": data.get("jobExecutionId"),
                    "total": data.get("total"),
                    "skipped": data.get("skipped"),
                    "written": data.get("written"),
                    "filename": data.get("filename"),
                    "created": data.get("created")
                }
            else:
                logger.error(f"Failed to retrieve pointing import data: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Error retrieving pointing import data: {e}")
            return {}

    def get_pointing_import_lines(self, page: int = 0, size: int = 10000) -> List[Dict[str, Any]]:
        """Get pointing import lines (typically error records)."""
        if not self._company_id:
            if not self.initialize():
                return []

        try:
            headers = self.get_auth_headers()

            params = {
                'page': page,
                'size': size
            }

            response = self.session.get(
                f"{self.api_url}/pay/api/companies/{self._company_id}/pointing-imports/lines",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                logger.info("Pointing import lines retrieved successfully.")
                return [
                    {
                        "recordId": line.get("recordId"),
                        "errors": line.get("errors"),
                    }
                    for line in data
                ]
            else:
                logger.error(f"Failed to retrieve pointing import lines: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error retrieving pointing import lines: {e}")
            return []

    def get_pointings_with_job_id(self, job_execution_id: str) -> List[str]:
        """Get pointings associated with a job execution ID."""
        if not self._company_id:
            if not self.initialize():
                return []

        try:
            headers = self.get_auth_headers()

            params = {
                'jobExecutionId': job_execution_id,
            }

            response = self.session.get(
                f"{self.api_url}/pay/api/companies/{self._company_id}/pointings",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                logger.info("Pointings data retrieved successfully.")
                return self._transform_pointing_data(data)
            else:
                logger.error(f"Failed to retrieve pointings: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error retrieving pointings: {e}")
            return []

    def _transform_pointing_data(self, pointings: List[Dict[str, Any]]) -> List[str]:
        """Transform pointing data to extract timestamps."""
        result = []

        # Extract entrance and exit timestamps
        for pointing in pointings:
            if pointing.get("entrance"):
                result.append(pointing.get("entrance"))
            if pointing.get("exit"):
                result.append(pointing.get("exit"))

        return result