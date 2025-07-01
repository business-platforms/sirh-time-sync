import logging
import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk
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
from src.update_checker import UpdateChecker
from src.util.paths import get_log_file_path, initialize_app_directories

logger = logging.getLogger(__name__)


class Application:
    """Main application class that coordinates all service."""

    def __init__(self):
        self.container = DependencyContainer()
        self._running = False  # Track running state
        self.setup_logging()
        self.initialize_database()
        self.setup_dependencies()

        self.update_checker = UpdateChecker(self.container.get('config_repository'),
                                            "https://timesync-dev.rh-partner.com/api/updates")

        # Check for completed updates on startup
        self.verify_update_on_startup()

    def verify_update_on_startup(self):
        """Check if an update was completed and notify user."""
        try:
            verification_result = self.update_checker.verify_update_completion()

            if verification_result['update_completed']:
                if verification_result['success']:
                    logger.info(f"Update verification: {verification_result['message']}")
                    # Don't show popup immediately on startup, just log success
                    # The main window can show a notification if needed
                else:
                    logger.warning(f"Update may have failed: {verification_result['message']}")
                    # You might want to handle failed updates here

        except Exception as e:
            logger.error(f"Error during startup update verification: {e}")

    def show_update_success_notification(self, parent_window=None):
        """Show update success notification if there was a recent update."""
        try:
            verification_result = self.update_checker.verify_update_completion()

            if verification_result['update_completed'] and verification_result['success']:
                if parent_window:
                    messagebox.showinfo(
                        "Mise à jour réussie",
                        f"L'application a été mise à jour avec succès!\n\n{verification_result['message']}",
                        parent=parent_window
                    )
                else:
                    # Create temporary window for notification
                    temp_window = tk.Tk()
                    temp_window.withdraw()
                    messagebox.showinfo(
                        "Mise à jour réussie",
                        f"L'application a été mise à jour avec succès!\n\n{verification_result['message']}"
                    )
                    temp_window.destroy()

        except Exception as e:
            logger.error(f"Error showing update success notification: {e}")

    def initialize_database(self):
        """Initialize the database schema."""
        db_initializer = DatabaseInitializer()
        if not db_initializer.run_initialization():
            logger.error("Failed to initialize database. Application may not function correctly.")

    def setup_logging(self) -> None:
        """Set up logging configuration using centralized path management."""
        try:
            # Initialize all application directories first
            app_dirs = initialize_app_directories()

            # Get the log file path using centralized path management
            log_file_path = get_log_file_path()

            # Configure logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file_path, encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )

            # Log successful initialization
            logger.info("Application logging initialized successfully")
            logger.info(f"Log file: {log_file_path}")
            logger.info(f"Application directories initialized: {list(app_dirs.keys())}")

        except Exception as e:
            # Fallback to basic console logging if file logging fails
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )
            print(f"Warning: Failed to setup file logging: {e}")
            print("Falling back to console-only logging")

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

    def check_for_updates(self, show_if_none=False):
        """Check for application updates."""

        def _check():
            result = self.update_checker.check_for_updates()

            if result.get("available", False):
                # Check prerequisites first
                file_size = result.get("file_size", 0)
                if file_size > 0:
                    prereq_ok, prereq_msg = self.update_checker.check_update_prerequisites(file_size)
                    if not prereq_ok:
                        tk.messagebox.showerror(
                            "Mise à jour impossible",
                            f"Impossible de mettre à jour: {prereq_msg}"
                        )
                        return

                # We have an update
                if tk.messagebox.askyesno(
                        "Mise à jour disponible",
                        f"Une nouvelle version ({result['version']}) est disponible. Voulez-vous mettre à jour maintenant ?\n\n"
                        f"Notes de version :\n{result['notes']}"
                ):
                    self.apply_update(result["url"], result["download_token"])
            elif show_if_none:
                tk.messagebox.showinfo(
                    "Aucune mise à jour",
                    f"Vous utilisez la dernière version ({self.update_checker.current_version})."
                )

        # Run in background thread
        threading.Thread(target=_check, daemon=True).start()

    def check_for_mandatory_updates(self, parent_window=None) -> bool:
        """
        Check for updates and require the user to update if available.
        Returns True if no update is needed or update was successful.
        Returns False if update was available but not applied.
        """
        result = self.update_checker.check_for_updates()

        if result.get("available", False):
            # Check prerequisites first
            file_size = result.get("file_size", 0)
            if file_size > 0:
                prereq_ok, prereq_msg = self.update_checker.check_update_prerequisites(file_size)
                if not prereq_ok:
                    if parent_window:
                        tk.messagebox.showerror(
                            "Mise à jour impossible",
                            f"Impossible de mettre à jour: {prereq_msg}\n\nL'application va se fermer.",
                            parent=parent_window
                        )
                    return False

            # Create or use the provided parent window for the dialog
            if not parent_window:
                temp_window = tk.Tk()
                temp_window.withdraw()
            else:
                temp_window = parent_window

            # Show mandatory update dialog
            message = (
                f"Une mise à jour importante (version {result['version']}) est disponible.\n\n"
                f"Vous devez installer cette mise à jour pour continuer.\n\n"
                f"Notes de version :\n{result['notes']}"
            )

            update_choice = tk.messagebox.askquestion(
                "Mise à jour obligatoire",
                message,
                icon='warning'
            )

            if update_choice == 'yes':
                # Start update process
                return self.apply_mandatory_update(result["url"], result["download_token"])
            else:
                # User declined update, exit application
                if not parent_window:
                    temp_window.destroy()
                return False

        return True  # No update available or update not required

    def apply_update(self, url, download_token):
        """Download and apply the update with progress reporting."""

        def _update():
            # Create progress window with more details
            progress_window = tk.Toplevel()
            progress_window.title("Mise à jour en cours")
            progress_window.geometry("450x180")
            progress_window.resizable(False, False)
            # progress_window.transient(self.root)
            progress_window.grab_set()

            # Center the window
            progress_window.update_idletasks()
            width = progress_window.winfo_width()
            height = progress_window.winfo_height()
            x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
            y = (progress_window.winfo_screenheight() // 2) - (height // 2)
            progress_window.geometry(f"{width}x{height}+{x}+{y}")

            # Status label
            status_label = tk.Label(
                progress_window,
                text="Téléchargement de la mise à jour...",
                font=("Segoe UI", 10),
                pady=10
            )
            status_label.pack()

            # Progress bar
            progress_bar = ttk.Progressbar(
                progress_window,
                orient="horizontal",
                length=400,
                mode="determinate"
            )
            progress_bar.pack(pady=10, padx=20)

            # Progress percentage
            percent_label = tk.Label(
                progress_window,
                text="0%",
                font=("Segoe UI", 9)
            )
            percent_label.pack()

            # Progress callback
            def update_progress(percent):
                progress_bar["value"] = percent
                percent_label.config(text=f"{percent}%")
                progress_window.update()

            try:
                # Download update
                installer_path = self.update_checker.download_update(url, update_progress)

                if installer_path:
                    # Update UI for installation phase
                    status_label.config(text="Installation en cours...")
                    progress_bar.config(mode="indeterminate")
                    progress_bar.start()
                    percent_label.config(text="L'application redémarrera automatiquement.")
                    progress_window.update()

                    # Stop services before updating
                    self.stop_service()

                    # Apply update
                    if self.update_checker.apply_update(installer_path):
                        # Give installer time to start before exiting
                        import time
                        time.sleep(2)

                        # Exit application to allow installer to run
                        import sys
                        sys.exit(0)
                    else:
                        progress_window.destroy()
                        tk.messagebox.showerror(
                            "Échec de la mise à jour",
                            "Échec de l'installation de la mise à jour. Veuillez réessayer."
                        )
                else:
                    progress_window.destroy()
                    tk.messagebox.showerror(
                        "Échec de la mise à jour",
                        "Échec du téléchargement de la mise à jour. Veuillez réessayer plus tard."
                    )
            except Exception as e:
                progress_window.destroy()
                tk.messagebox.showerror(
                    "Erreur de mise à jour",
                    f"Une erreur s'est produite pendant la mise à jour: {str(e)}"
                )
                logger.error(f"Error during update process: {e}")

        # Run in background thread
        threading.Thread(target=_update, daemon=True).start()

    def apply_mandatory_update(self, url, download_token):
        """Download and apply a mandatory update with progress reporting."""
        # Create progress window
        progress_window = tk.Tk()
        progress_window.title("Mise à jour obligatoire en cours")
        progress_window.geometry("450x180")
        progress_window.resizable(False, False)
        progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Prevent closing

        # Center the window
        progress_window.update_idletasks()
        width = progress_window.winfo_width()
        height = progress_window.winfo_height()
        x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
        y = (progress_window.winfo_screenheight() // 2) - (height // 2)
        progress_window.geometry(f"{width}x{height}+{x}+{y}")

        # Status label
        status_label = tk.Label(
            progress_window,
            text="Téléchargement de la mise à jour...",
            font=("Segoe UI", 10),
            pady=10
        )
        status_label.pack()

        # Progress bar
        progress_bar = ttk.Progressbar(
            progress_window,
            orient="horizontal",
            length=400,
            mode="determinate"
        )
        progress_bar.pack(pady=10, padx=20)

        # Progress percentage
        percent_label = tk.Label(
            progress_window,
            text="0%",
            font=("Segoe UI", 9)
        )
        percent_label.pack()

        # Progress callback
        def update_progress(percent):
            progress_bar["value"] = percent
            percent_label.config(text=f"{percent}%")
            progress_window.update()

        try:
            # Download update
            installer_path = self.update_checker.download_update(url, update_progress)

            if installer_path:
                # Update UI for installation phase
                status_label.config(text="Installation en cours...")
                progress_bar.config(mode="indeterminate")
                progress_bar.start()
                percent_label.config(text="L'application redémarrera automatiquement.")
                progress_window.update()

                # Stop services before updating
                self.stop_service()

                # Apply update
                if self.update_checker.apply_update(installer_path):
                    # Give installer time to start before exiting
                    import time
                    time.sleep(2)

                    # Exit application to allow installer to run
                    import sys
                    sys.exit(0)
                else:
                    progress_window.destroy()
                    tk.messagebox.showerror(
                        "Échec de la mise à jour",
                        "Échec de l'installation de la mise à jour. L'application va se fermer."
                    )
                    return False
            else:
                progress_window.destroy()
                tk.messagebox.showerror(
                    "Échec de la mise à jour",
                    "Échec du téléchargement de la mise à jour. L'application va se fermer."
                )
                return False
        except Exception as e:
            progress_window.destroy()
            tk.messagebox.showerror(
                "Erreur de mise à jour",
                f"Une erreur s'est produite: {str(e)}. L'application va se fermer."
            )
            logger.error(f"Error during mandatory update: {e}")
            return False