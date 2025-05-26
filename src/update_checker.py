# src/update_checker.py
import os
import sys
import requests
import logging
import tempfile
import shutil
import subprocess
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
                    "notes": data.get("notes", "")
                }
            else:
                logger.error(f"Error checking for updates: {response.status_code}")
                return {"available": False}

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return {"available": False}

    def download_update(self, url: str,  progress_callback=None) -> Optional[str]:
        """Download update file to temporary location with progress reporting."""
        try:
            # Start download with streaming
            logger.debug(f"Initiating GET request to {url} with streaming enabled and a 60-second timeout.")
            response = requests.get(url, stream=True, timeout=500)

            # Log HTTP status code
            if response.status_code != 200:
                logger.error(f"Failed to download update. HTTP status code: {response.status_code}. Response content: {response.text[:200]}...")
                return None
            logger.info(f"Successfully connected to the update server. HTTP status code: {response.status_code}.")

            # Get total size
            total_size = int(response.headers.get('content-length', 0))
            if total_size == 0:
                logger.warning("Content-Length header not found or is zero. Cannot report accurate download progress.")
            else:
                logger.info(f"Total update file size: {total_size} bytes.")

            # Create temp file with .exe extension
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
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
                                if chunk_num % 100 == 0 or downloaded == total_size: # Log every 100 chunks or when finished
                                    logger.debug(f"Download progress: {progress}% ({downloaded}/{total_size} bytes).")
                                progress_callback(progress)
                logger.info(f"File download complete. Total bytes downloaded: {downloaded}.")
            except IOError as e:
                logger.error(f"Error writing to temporary file {temp_file.name} during download: {e}")
                os.remove(temp_file.name)
                return None


            # Verify checksum
            checksum = response.headers.get('X-Content-Checksum')
            logger.info(f"Verifying checksum for downloaded file: {temp_file.name}")
            computed_checksum = compute_sha256(temp_file.name)
            if computed_checksum.lower() != checksum.lower():
                logger.error(f"Checksum mismatch for {temp_file.name}. Expected: {checksum}, Got: {computed_checksum}. Deleting corrupt file.")
                os.remove(temp_file.name)
                return None
            logger.info(f"Checksum verification successful. Downloaded file integrity confirmed.")

            logger.info(f"Update successfully downloaded and verified to {temp_file.name}")
            return temp_file.name

        except requests.exceptions.Timeout:
            logger.error("Download timed out after 60 seconds. This might indicate a slow network connection or an unresponsive server.")
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.remove(temp_file.name)
                logger.debug(f"Removed incomplete download file: {temp_file.name}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error occurred. Unable to reach the update server. Details: {e}")
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.remove(temp_file.name)
                logger.debug(f"Removed incomplete download file: {temp_file.name}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An unexpected request-related error occurred during download: {e}")
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.remove(temp_file.name)
                logger.debug(f"Removed incomplete download file: {temp_file.name}")
            return None
        except Exception as e:
            logger.critical(f"An unhandled critical error occurred during the update download process: {e}", exc_info=True)
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.remove(temp_file.name)
                logger.debug(f"Removed incomplete download file: {temp_file.name}")
            return None


    def apply_update(self, installer_path: str) -> bool:
        """Run the installer to apply the update."""
        try:
            # Get application directory
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # # Get the current database path (now in AppData)
            # db_path = get_database_path()
            #
            # # Create backup directory in application folder
            # backup_dir = os.path.join(app_dir, "backup")
            # os.makedirs(backup_dir, exist_ok=True)
            #
            # # Backup database if it exists
            # if os.path.exists(db_path):
            #     backup_name = f"attendance.db_backup_{self.current_version}"
            #     backup_path = os.path.join(backup_dir, backup_name)
            #
            #     try:
            #         shutil.copy2(db_path, backup_path)
            #         logger.info(f"Database backed up from {db_path} to {backup_path}")
            #     except Exception as backup_error:
            #         logger.error(f"Failed to backup database: {backup_error}")
            # else:
            #     logger.warning(f"Database not found at {db_path}, no backup created")

            # Run installer silently
            subprocess.Popen([
                installer_path,
                "/VERYSILENT",  # No UI during installation
                "/NORESTART",  # Don't restart Windows
                "/CLOSEAPPLICATIONS",  # Close the application if running
                "/RESTARTAPPLICATIONS"  # Restart the application after update
            ])

            logger.info("Update started, application will restart")
            return True

        except Exception as e:
            logger.error(f"Error applying update: {e}")
            return False