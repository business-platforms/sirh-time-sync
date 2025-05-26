# src/update_checker.py
import os
import sys
import requests
import logging
import tempfile
import shutil
import subprocess
import time
import atexit
from pathlib import Path
from typing import Dict, Any, Optional

from src.data.repositories import ConfigRepository
from src.util.compute_checksum import compute_sha256
from src.util.paths import get_database_path  # Import our database path function

logger = logging.getLogger(__name__)


class UpdateChecker:
    """Checks for and applies updates to the application."""

    def __init__(self, config_repository: ConfigRepository, update_url: str):
        self.config_repository = config_repository
        self.update_url = update_url
        self.current_version = self._get_current_version()

    def _get_current_version(self) -> str:
        """Get the current version of the application."""
        try:
            # Get path to version.txt relative to executable
            if getattr(sys, 'frozen', False):
                # Running as executable
                app_dir = os.path.dirname(sys.executable)
                version_path = os.path.join(app_dir, "version.txt")
            else:
                # Running as script
                app_dir = os.path.dirname(os.path.abspath(__file__))
                version_path = os.path.join(os.path.dirname(app_dir), "version.txt")

            if os.path.exists(version_path):
                with open(version_path, "r") as f:
                    return f.read().strip()
            else:
                logger.warning("Version file not found")
                return "0.0.0"
        except Exception as e:
            logger.error(f"Error getting current version: {e}")
            return "0.0.0"

    def check_for_updates(self) -> Dict[str, Any]:
        """Check for available updates."""
        config = self.config_repository.get_config()
        try:

            headers = {
                'email': config.api_username,
                'secret-key': config.api_secret_key
            }

            response = requests.get(f"{self.update_url}/check",
                                    params={"version": self.current_version},
                                    headers=headers,
                                    timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "available": data.get("update_available", False),
                    "version": data.get("version", ""),
                    "download_token": data.get("download_token", "?"),
                    "url": data.get("download_url", ""),
                    "notes": data.get("notes", ""),
                    "file_size": data.get("file_size", 0)  # Add file size for prerequisite checks
                }
            else:
                logger.error(f"Error checking for updates: {response.status_code}")
                return {"available": False}

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return {"available": False}

    def check_update_prerequisites(self, file_size: int) -> tuple[bool, str]:
        """Check if system meets update requirements."""
        try:
            # Check available disk space (need space for download + installation)
            temp_dir = tempfile.gettempdir()
            free_space = shutil.disk_usage(temp_dir).free
            required_space = file_size * 3  # Download + extraction + safety margin

            if free_space < required_space:
                error_msg = f"Insufficient disk space. Required: {required_space // 1024 // 1024}MB, Available: {free_space // 1024 // 1024}MB"
                logger.error(error_msg)
                return False, error_msg

            # Check if we can write to temp directory
            test_file = os.path.join(temp_dir, 'timesync_write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                error_msg = f"Cannot write to temporary directory: {e}"
                logger.error(error_msg)
                return False, error_msg

            # Check if update is already in progress
            update_lock = os.path.join(temp_dir, 'timesync_update_lock')
            if os.path.exists(update_lock):
                error_msg = "Another update is already in progress"
                logger.warning(error_msg)
                return False, error_msg

            return True, "Prerequisites check passed"

        except Exception as e:
            error_msg = f"Error checking prerequisites: {e}"
            logger.error(error_msg)
            return False, error_msg

    def download_update(self, url: str, progress_callback=None) -> Optional[str]:
        """Download update file to temporary location with progress reporting."""
        update_lock = None
        temp_file = None

        try:
            # Create update lock file
            temp_dir = tempfile.gettempdir()
            update_lock = os.path.join(temp_dir, 'timesync_update_lock')
            with open(update_lock, 'w') as f:
                f.write(f"Update started at {time.time()}")

            # Start download with streaming
            logger.debug(f"Initiating GET request to {url} with streaming enabled and a 500-second timeout.")
            response = requests.get(url, stream=True, timeout=500)

            # Log HTTP status code
            if response.status_code != 200:
                logger.error(
                    f"Failed to download update. HTTP status code: {response.status_code}. Response content: {response.text[:200]}...")
                return None
            logger.info(f"Successfully connected to the update server. HTTP status code: {response.status_code}.")

            # Get total size
            total_size = int(response.headers.get('content-length', 0))
            if total_size == 0:
                logger.warning("Content-Length header not found or is zero. Cannot report accurate download progress.")
            else:
                logger.info(f"Total update file size: {total_size} bytes.")

            # Create temp file with .exe extension in a dedicated update directory
            update_dir = os.path.join(temp_dir, 'timesync_updates')
            os.makedirs(update_dir, exist_ok=True)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe', dir=update_dir)
            temp_file.close()
            logger.info(f"Created temporary file for download: {temp_file.name}")

            # Download with progress updates
            downloaded = 0
            try:
                with open(temp_file.name, 'wb') as f:
                    logger.debug("Starting file download in chunks.")
                    for chunk_num, chunk in enumerate(response.iter_content(chunk_size=8192)):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size > 0:
                                progress = int(downloaded * 100 / total_size)
                                # Log progress at certain intervals to avoid excessive logging
                                if chunk_num % 100 == 0 or downloaded == total_size:  # Log every 100 chunks or when finished
                                    logger.debug(f"Download progress: {progress}% ({downloaded}/{total_size} bytes).")
                                progress_callback(progress)
                logger.info(f"File download complete. Total bytes downloaded: {downloaded}.")
            except IOError as e:
                logger.error(f"Error writing to temporary file {temp_file.name} during download: {e}")
                self._safe_remove(temp_file.name)
                return None

            # Verify file size
            actual_size = os.path.getsize(temp_file.name)
            if total_size > 0 and actual_size != total_size:
                logger.error(f"Downloaded file size mismatch. Expected: {total_size}, Got: {actual_size}")
                self._safe_remove(temp_file.name)
                return None

            # Verify checksum if provided
            checksum = response.headers.get('X-Content-Checksum')
            if checksum:
                logger.info(f"Verifying checksum for downloaded file: {temp_file.name}")
                computed_checksum = compute_sha256(temp_file.name)
                if computed_checksum.lower() != checksum.lower():
                    logger.error(
                        f"Checksum mismatch for {temp_file.name}. Expected: {checksum}, Got: {computed_checksum}. Deleting corrupt file.")
                    self._safe_remove(temp_file.name)
                    return None
                logger.info(f"Checksum verification successful. Downloaded file integrity confirmed.")

            # Schedule cleanup on application exit
            atexit.register(self._cleanup_temp_files)

            logger.info(f"Update successfully downloaded and verified to {temp_file.name}")
            return temp_file.name

        except requests.exceptions.Timeout:
            logger.error(
                "Download timed out after 500 seconds. This might indicate a slow network connection or an unresponsive server.")
            if temp_file and os.path.exists(temp_file.name):
                self._safe_remove(temp_file.name)
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error occurred. Unable to reach the update server. Details: {e}")
            if temp_file and os.path.exists(temp_file.name):
                self._safe_remove(temp_file.name)
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An unexpected request-related error occurred during download: {e}")
            if temp_file and os.path.exists(temp_file.name):
                self._safe_remove(temp_file.name)
            return None
        except Exception as e:
            logger.critical(f"An unhandled critical error occurred during the update download process: {e}",
                            exc_info=True)
            if temp_file and os.path.exists(temp_file.name):
                self._safe_remove(temp_file.name)
            return None
        finally:
            # Clean up lock file
            if update_lock:
                self._safe_remove(update_lock)

    def apply_update(self, installer_path: str) -> bool:
        """Run the installer to apply the update with improved error handling."""
        verification_file = None
        install_log = None

        try:
            # Get application directory
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # Create verification file to track update progress
            temp_dir = tempfile.gettempdir()
            verification_file = os.path.join(temp_dir, 'timesync_update_pending')

            with open(verification_file, 'w') as f:
                f.write(f"updating_from_{self.current_version}_to_new_version_{time.time()}")

            # Create installation log path
            install_log = os.path.join(temp_dir, 'timesync_install.log')

            logger.info(f"Starting installer: {installer_path}")
            logger.info(f"Installation log will be written to: {install_log}")
            logger.info(f"Update verification file: {verification_file}")

            # Prepare installer arguments
            installer_args = [
                installer_path,
                "/VERYSILENT",  # No UI during installation
                "/NORESTART",  # Don't restart Windows
                "/CLOSEAPPLICATIONS",  # Close the application if running
                "/RESTARTAPPLICATIONS",  # Restart the application after update
                f"/LOG={install_log}",  # Create installation log
                "/SUPPRESSMSGBOXES"  # Don't show message boxes
            ]

            # Start the installer process
            logger.info("Launching installer process...")
            process = subprocess.Popen(
                installer_args,
                cwd=os.path.dirname(installer_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait a short time for the installer to start and validate
            try:
                # Wait up to 15 seconds for installer to start
                return_code = process.wait(timeout=15)
                logger.info(f"Installer process completed with return code: {return_code}")

                if return_code == 0:
                    logger.info("Installer started successfully")
                    # Schedule cleanup of installer file after a delay
                    self._schedule_delayed_cleanup(installer_path, 60)  # Clean up after 60 seconds
                    return True
                else:
                    logger.error(f"Installer failed with return code: {return_code}")
                    self._cleanup_failed_update(installer_path, verification_file)
                    return False

            except subprocess.TimeoutExpired:
                # Installer is still running after 15 seconds, which is normal for background installation
                logger.info("Installer is running in background (this is normal)")
                # The installer will handle the rest, including application restart
                self._schedule_delayed_cleanup(installer_path, 120)  # Clean up after 2 minutes
                return True

        except FileNotFoundError:
            logger.error(f"Installer file not found: {installer_path}")
            self._cleanup_failed_update(installer_path, verification_file)
            return False
        except PermissionError as e:
            logger.error(f"Permission denied running installer: {e}")
            self._cleanup_failed_update(installer_path, verification_file)
            return False
        except Exception as e:
            logger.error(f"Error applying update: {e}")
            self._cleanup_failed_update(installer_path, verification_file)
            return False

    def _schedule_delayed_cleanup(self, installer_path: str, delay_seconds: int):
        """Schedule cleanup of installer file after a delay."""

        def delayed_cleanup():
            time.sleep(delay_seconds)
            self._safe_remove(installer_path)
            logger.info(f"Cleaned up installer file: {installer_path}")

        import threading
        cleanup_thread = threading.Thread(target=delayed_cleanup, daemon=True)
        cleanup_thread.start()

    def _cleanup_failed_update(self, installer_path: str, verification_file: str = None):
        """Clean up after failed update."""
        logger.info("Cleaning up after failed update")

        self._safe_remove(installer_path)

        if verification_file:
            self._safe_remove(verification_file)

        # Clean up any update lock files
        temp_dir = tempfile.gettempdir()
        update_lock = os.path.join(temp_dir, 'timesync_update_lock')
        self._safe_remove(update_lock)

    def _cleanup_temp_files(self):
        """Clean up temporary files and directories."""
        temp_dir = tempfile.gettempdir()
        update_dir = os.path.join(temp_dir, 'timesync_updates')

        try:
            if os.path.exists(update_dir):
                shutil.rmtree(update_dir)
                logger.debug(f"Cleaned up update directory: {update_dir}")
        except Exception as e:
            logger.warning(f"Could not clean up update directory {update_dir}: {e}")

    def _safe_remove(self, file_path: str):
        """Safely remove a file without raising exceptions."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Removed file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not remove file {file_path}: {e}")

    def verify_update_completion(self) -> Dict[str, Any]:
        """Verify if an update was completed successfully."""
        temp_dir = tempfile.gettempdir()
        verification_file = os.path.join(temp_dir, 'timesync_update_pending')
        completion_file = os.path.join(temp_dir, 'timesync_update_complete')

        result = {
            'update_completed': False,
            'previous_version': None,
            'success': False,
            'message': 'No update detected'
        }

        try:
            # Check if update was completed
            if os.path.exists(completion_file):
                try:
                    with open(completion_file, 'r') as f:
                        content = f.read().strip()

                    result['update_completed'] = True
                    result['success'] = True
                    result['message'] = f'Update completed successfully: {content}'

                    # Clean up completion file
                    self._safe_remove(completion_file)
                    logger.info(f"Update verification successful: {content}")

                except Exception as e:
                    logger.error(f"Error reading completion file: {e}")
                    result['message'] = f'Error verifying update completion: {e}'

            # Check if update was pending but didn't complete
            elif os.path.exists(verification_file):
                try:
                    with open(verification_file, 'r') as f:
                        content = f.read().strip()

                    # Extract previous version from content
                    if 'updating_from_' in content:
                        parts = content.split('_')
                        if len(parts) >= 3:
                            result['previous_version'] = parts[2]

                    result['update_completed'] = True
                    result['success'] = False
                    result['message'] = f'Update may have failed: {content}'

                    # Clean up pending file
                    self._safe_remove(verification_file)
                    logger.warning(f"Found pending update that may have failed: {content}")

                except Exception as e:
                    logger.error(f"Error reading verification file: {e}")
                    result['message'] = f'Error checking update status: {e}'

            return result

        except Exception as e:
            logger.error(f"Error verifying update completion: {e}")
            result['message'] = f'Error during update verification: {e}'
            return result