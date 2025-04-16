# main.py
import sys
import argparse
from src.application import Application
from src.ui.main_window import MainWindow


def main():
    """Main entry point for the attendance system application."""
    parser = argparse.ArgumentParser(description='Attendance System')
    parser.add_argument('--config', action='store_true', help='Show configuration interface only')
    parser.add_argument('--start', action='store_true', help='Start the collectors in command line mode')
    parser.add_argument('--stop', action='store_true', help='Stop the collectors in command line mode')
    args = parser.parse_args()

    # Create the application
    app = Application()

    if args.config:
        # Run only the configuration window
        from src.ui.config_interface import ConfigInterface
        config_window = ConfigInterface(None, app.container.get('config_repository'))
        config_window.root.mainloop()
    elif args.start:
        # Start service in command line mode
        if app.start_service():
            print("Attendance system started successfully")
            try:
                # Keep running until interrupted
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Stopping attendance system...")
                app.stop_service()
        else:
            print("Failed to start the attendance system")
    elif args.stop:
        # Stop service in command line mode
        app.stop_service()
        print("Attendance system stopped")
    else:
        # Start the GUI application
        window = MainWindow(app)
        window.start()


if __name__ == "__main__":
    sys.exit(main() or 0)