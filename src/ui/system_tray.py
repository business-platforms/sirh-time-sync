# src/ui/system_tray.py
import os
import sys
import logging
import tempfile
import threading
import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class SystemTrayManager:
    """Manages the system tray icon and functionality."""

    def __init__(self, app, show_callback, exit_callback):
        """
        Initialize the system tray manager.

        Args:
            app: The application instance
            show_callback: Callback to show the main window
            exit_callback: Callback to exit the application
        """
        self.app = app
        self.show_callback = show_callback
        self.exit_callback = exit_callback
        self.icon = None
        self.tray_thread = None

        # Setup the system tray icon
        self.setup()

    def setup(self):
        """Setup the system tray icon and menu."""
        try:
            # Get icon path
            icon_path = self.resource_path("assets/timesync-logo.ico")
            if not os.path.exists(icon_path):
                # Fallback to PNG if ICO not available
                icon_path = self.resource_path("assets/timesync-logo.png")
                if not os.path.exists(icon_path):
                    # Create a blank image if icon files aren't available
                    icon_path = self.create_default_icon()

            # Load the icon image
            icon_image = Image.open(icon_path)

            # Define menu items
            menu = (
                pystray.MenuItem('Show Window', self.show_window),
                pystray.MenuItem('Start Service', self.start_service),
                pystray.MenuItem('Stop Service', self.stop_service),
                pystray.MenuItem('Exit', self.exit_app)
            )

            # Create the icon
            self.icon = pystray.Icon("timesync", icon_image, "Time Attendance System", menu)

            # Start the icon in a separate thread
            self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
            self.tray_thread.start()

            logger.info("System tray icon initialized")
        except Exception as e:
            logger.error(f"Failed to setup system tray icon: {e}")

    def create_default_icon(self):
        """Create a default icon if none is available."""
        try:
            img = Image.new('RGB', (64, 64), color=(36, 57, 142))
            d = ImageDraw.Draw(img)
            d.text((20, 20), "TS", fill=(255, 255, 255))
            temp_path = os.path.join(tempfile.gettempdir(), 'temp_icon.png')
            img.save(temp_path)
            return temp_path
        except Exception as e:
            logger.error(f"Failed to create default icon: {e}")
            return None

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def show_window(self, icon=None, item=None):
        """Show the main window."""
        if self.show_callback:
            self.show_callback()

    def start_service(self, icon=None, item=None):
        """Start the application service."""
        if not self.app.is_running():
            self.app.start_service()
            # Show notification
            if self.icon:
                self.icon.notify("Service started successfully")

    def stop_service(self, icon=None, item=None):
        """Stop the application service."""
        if self.app.is_running():
            self.app.stop_service()
            # Show notification
            if self.icon:
                self.icon.notify("Service stopped")

    def exit_app(self, icon=None, item=None):
        """Exit the application properly."""
        # Stop the icon
        if self.icon:
            self.icon.stop()

        # Call the exit callback
        if self.exit_callback:
            self.exit_callback()

    def notify(self, message):
        """Show a notification from the system tray."""
        if self.icon:
            self.icon.notify(message)

    def update_menu(self):
        """Update the system tray menu based on application state."""
        # This would need to be implemented if we want dynamic menu items
        pass

    def cleanup(self):
        """Clean up resources."""
        if self.icon:
            self.icon.stop()