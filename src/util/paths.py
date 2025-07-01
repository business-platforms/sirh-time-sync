import os
import sys


def get_persistent_data_path():
    """Get a persistent path for application data."""
    # If running as PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # When running as compiled exe
        if os.name == 'nt':  # Windows
            app_data = os.environ.get('APPDATA')
            if app_data:
                data_dir = os.path.join(app_data, "timesync")
            else:
                # Fallback to directory containing exe
                data_dir = os.path.join(os.path.dirname(sys.executable), "data")
        else:
            # For Linux
            home = os.path.expanduser("~")
            data_dir = os.path.join(home, ".config", "timesync")
    else:
        # When running from source, use the project directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, "data")

    # Ensure directory exists
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_database_path():
    """Get the path to the database file."""
    return os.path.join(get_persistent_data_path(), "attendance.db")


def get_logs_path():
    """Get the path to the logs directory."""
    logs_dir = os.path.join(get_persistent_data_path(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def get_exports_path():
    """Get the path to the exports directory."""
    exports_dir = os.path.join(get_persistent_data_path(), "exports")
    os.makedirs(exports_dir, exist_ok=True)
    return exports_dir


def get_backup_path():
    """Get the path to the backup directory."""
    backup_dir = os.path.join(get_persistent_data_path(), "backup")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def get_temp_path():
    """Get the path for temporary files within the app data directory."""
    temp_dir = os.path.join(get_persistent_data_path(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def get_log_file_path(filename_prefix="attendance_system"):
    """Get a full path for a log file with timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.log"
    return os.path.join(get_logs_path(), filename)


def get_export_file_path(filename):
    """Get a full path for an export file."""
    return os.path.join(get_exports_path(), filename)


def get_backup_file_path(filename):
    """Get a full path for a backup file."""
    return os.path.join(get_backup_path(), filename)


def get_all_app_directories():
    """Get all application directories for initialization purposes."""
    return {
        'data': get_persistent_data_path(),
        'logs': get_logs_path(),
        'exports': get_exports_path(),
        'backup': get_backup_path(),
        'temp': get_temp_path(),
        'database': get_database_path()
    }


def initialize_app_directories():
    """Initialize all application directories. Call this on app startup."""
    directories = get_all_app_directories()
    for dir_name, dir_path in directories.items():
        if dir_name != 'database':  # database is a file, not a directory
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✓ Initialized {dir_name} directory: {dir_path}")
            except Exception as e:
                print(f"✗ Failed to initialize {dir_name} directory: {e}")
                raise
    return directories