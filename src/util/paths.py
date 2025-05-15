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