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
from src.util.paths import get_database_path  # Import our database path function

logger = logging.getLogger(__name__)


class UpdateChecker:
    """Checks for and applies updates to the application."""

    def __init__(self, update_url: str):
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
        try:
            response = requests.get(f"{self.update_url}/check",
                                    params={"version": self.current_version},
                                    timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "available": data.get("update_available", False),
                    "version": data.get("version", ""),
                    "url": data.get("download_url", ""),
                    "notes": data.get("notes", "")
                }
            else:
                logger.error(f"Error checking for updates: {response.status_code}")
                return {"available": False}

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return {"available": False}

    def download_update(self, url: str) -> Optional[str]:
        """Download update file to temporary location."""
        try:
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code != 200:
                logger.error(f"Failed to download update: {response.status_code}")
                return None

            # Create temp file with .exe extension
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
            temp_file.close()

            # Download file
            with open(temp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded update to {temp_file.name}")
            return temp_file.name

        except Exception as e:
            logger.error(f"Error downloading update: {e}")
            return None

    def apply_update(self, installer_path: str) -> bool:
        """Run the installer to apply the update."""
        try:
            # Get application directory
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # Get the current database path (now in AppData)
            db_path = get_database_path()

            # Create backup directory in application folder
            backup_dir = os.path.join(app_dir, "backup")
            os.makedirs(backup_dir, exist_ok=True)

            # Backup database if it exists
            if os.path.exists(db_path):
                backup_name = f"attendance.db_backup_{self.current_version}"
                backup_path = os.path.join(backup_dir, backup_name)

                try:
                    shutil.copy2(db_path, backup_path)
                    logger.info(f"Database backed up from {db_path} to {backup_path}")
                except Exception as backup_error:
                    logger.error(f"Failed to backup database: {backup_error}")
            else:
                logger.warning(f"Database not found at {db_path}, no backup created")

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