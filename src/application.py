# src/application.py
import logging
import os
from datetime import datetime
from typing import Dict, Any

from src.config.config import API_URL
from src.core.dependency_container import DependencyContainer
from src.core.config_service import ConfigurationService
from src.data.sqlite_repositories import (
    SQLiteConfigRepository, SQLiteAttendanceRepository, SQLiteLogRepository
)
from src.service.device_service import DeviceService
from src.service.api_service import APIService
from src.service.attendance_service import AttendanceService
from src.service.sync_service import SyncService
from src.service.scheduler_service import SchedulerService
from src.data.database_initializer import DatabaseInitializer

logger = logging.getLogger(__name__)


class Application:
    """Main application class that coordinates all service."""

    def __init__(self):
        self.container = DependencyContainer()
        self._running = False  # Track running state
        self.setup_logging()
        self.initialize_database()
        self.setup_dependencies()

    def initialize_database(self):
        """Initialize the database schema."""
        db_initializer = DatabaseInitializer()
        if not db_initializer.run_initialization():
            logger.error("Failed to initialize database. Application may not function correctly.")

    def setup_logging(self) -> None:
        """Set up logging configuration."""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/attendance_system_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )

    def setup_dependencies(self) -> None:
        """Set up dependency injection container."""
        # Configure API URL
        api_url = os.environ.get('API_URL', API_URL)

        # Register repositories
        self.container.register('config_repository', SQLiteConfigRepository())
        self.container.register('attendance_repository', SQLiteAttendanceRepository())
        self.container.register('log_repository', SQLiteLogRepository())

        # Register configuration service
        self.container.register('config_service', ConfigurationService(
            self.container.get('config_repository'),
            api_url
        ))

        # Register device service
        self.container.register('device_service', DeviceService(
            self.container.get('config_repository')
        ))

        # Register API service
        self.container.register('api_service', APIService(
            self.container.get('config_repository'),
            api_url
        ))

        # Register attendance service
        self.container.register('attendance_service', AttendanceService(
            self.container.get('attendance_repository'),
            self.container.get('log_repository'),
            self.container.get('device_service')
        ))

        # Register sync service
        self.container.register('sync_service', SyncService(
            self.container.get('api_service'),
            self.container.get('attendance_service'),
            self.container.get('device_service')
        ))

        # Register scheduler service
        self.container.register('scheduler_service', SchedulerService(
            self.container.get('config_repository')
        ))

        logger.info("Application dependencies initialized")

    def register_scheduled_jobs(self) -> None:
        """Register scheduled jobs with the scheduler service."""
        scheduler = self.container.get('scheduler_service')

        # Register attendance collection job
        scheduler.register_job(
            'attendance_collection',
            lambda: self.container.get('attendance_service').collect_attendance()
        )

        # Register attendance upload job
        scheduler.register_job(
            'attendance_upload',
            lambda: self.container.get('sync_service').upload_attendance_to_api()
        )

        # Register user import job
        scheduler.register_job(
            'user_import',
            lambda: self.container.get('sync_service').import_users_from_api_to_device()
        )

        logger.info("Scheduled jobs registered")

    def is_running(self) -> bool:
        """Check if the application services are currently running.

        Returns:
            bool: True if the system is running, False otherwise
        """
        return self._running

    def start_service(self) -> bool:
        """Start application service."""
        try:
            # Check if configuration exists
            config_service = self.container.get('config_service')
            config = config_service.get_config()

            if not config:
                logger.warning("No configuration found. Please configure the system first.")
                return False

            # Initialize device service
            device_service = self.container.get('device_service')
            if not device_service.initialize_connection():
                logger.error("Failed to initialize device connection")
                return False

            # Initialize API service
            api_service = self.container.get('api_service')
            if not api_service.initialize():
                logger.error("Failed to initialize API service")
                return False

            # Register and start scheduled jobs
            self.register_scheduled_jobs()
            scheduler = self.container.get('scheduler_service')
            scheduler.start()

            # Set running flag to true
            self._running = True

            logger.info("Application service started")
            return True

        except Exception as e:
            logger.error(f"Error starting service: {e}")
            return False

    def stop_service(self) -> None:
        """Stop application service."""
        try:
            # Stop scheduler
            scheduler = self.container.get('scheduler_service')
            scheduler.stop()

            # Disconnect device
            device_service = self.container.get('device_service')
            device_service.disconnect()

            # Set running flag to false
            self._running = False

            logger.info("Application service stopped")

        except Exception as e:
            logger.error(f"Error stopping service: {e}")

    def test_connections(self) -> Dict[str, Any]:
        """Test device and API connections."""
        results = {
            'device': {'success': False},
            'api': {'success': False},
            'overall': False
        }

        try:
            # Get configuration
            config_service = self.container.get('config_service')
            config = config_service.get_config()

            if not config:
                logger.warning("No configuration found for connection tests")
                return results

            # Test device connection
            device_result = config_service.test_device_connection(
                config.device_ip, config.device_port
            )
            results['device'] = device_result

            # Test API connection
            api_result = config_service.test_api_connection(
                config.company_id, config.api_username, config.api_password
            )
            results['api'] = api_result

            # Overall success
            results['overall'] = device_result['success'] and api_result['success']

            return results

        except Exception as e:
            logger.error(f"Error in connection tests: {e}")
            results['error'] = str(e)
            return results