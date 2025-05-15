#!/usr/bin/env python3
# ubuntu_build.py
import os
import sys
import subprocess
import shutil
import argparse
from datetime import datetime


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Build the Time Attendance System application for Ubuntu')
    parser.add_argument('--version', required=True, help='Version number (e.g., 1.0.0)')
    args = parser.parse_args()

    version = args.version
    print(f"Building Time Attendance System v{version} for Ubuntu")

    # Create version file
    with open("version.txt", "w") as f:
        f.write(version)

    # Clean previous build
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # Create necessary directories
    os.makedirs("dist", exist_ok=True)
    os.makedirs("installer_files", exist_ok=True)

    # Run PyInstaller build
    print("Running PyInstaller...")

    pyinstaller_args = [
        "main.py",
        "--name=TimeAttendanceSystem",
        "--onefile",
        "--windowed",
        "--add-data=assets:assets",
        "--add-data=src:src",
        "--add-data=version.txt:.",
        "--hidden-import=sqlite3",
        "--hidden-import=requests",
        "--hidden-import=zk",
        "--hidden-import=schedule",
        "--hidden-import=uuid",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=tkinter.simpledialog",
        "--hidden-import=pystray",
        "--hidden-import=PIL",
        "--distpath=./dist",
        "--workpath=./build",
    ]

    subprocess.check_call([sys.executable, "-m", "PyInstaller"] + pyinstaller_args)

    # Create necessary directories in the distribution directory
    os.makedirs("dist/logs", exist_ok=True)
    os.makedirs("dist/exports", exist_ok=True)
    os.makedirs("dist/backup", exist_ok=True)

    # Create desktop file
    print("Creating desktop file...")
    desktop_file = f"""[Desktop Entry]
Version={version}
Type=Application
Name=Time Attendance System
Comment=Time attendance tracking and synchronization
Exec=/opt/timeattendancesystem/TimeAttendanceSystem
Icon=/opt/timeattendancesystem/assets/timesync-logo.png
Terminal=false
Categories=Office;Utility;
"""
    with open("installer_files/timeattendancesystem.desktop", "w") as f:
        f.write(desktop_file)

    # Create install script
    print("Creating installation script...")
    install_script = """#!/bin/bash
# Installation script for Time Attendance System

# Exit on error
set -e

# Define constants
APP_NAME="TimeAttendanceSystem"
INSTALL_DIR="/opt/timeattendancesystem"
BIN_LINK="/usr/local/bin/timeattendancesystem"
DESKTOP_FILE="/usr/share/applications/timeattendancesystem.desktop"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

echo "Installing Time Attendance System..."

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Copy application files
cp -r ./* "$INSTALL_DIR/"

# Make executable
chmod +x "$INSTALL_DIR/$APP_NAME"

# Create symlink in /usr/local/bin
ln -sf "$INSTALL_DIR/$APP_NAME" "$BIN_LINK"

# Install desktop file
cp "./timeattendancesystem.desktop" "$DESKTOP_FILE"
update-desktop-database /usr/share/applications

echo "Installation completed successfully!"
echo "You can now launch the application from your applications menu or run 'timeattendancesystem' from terminal."
"""
    with open("installer_files/install.sh", "w") as f:
        f.write(install_script)

    # Make install script executable
    os.chmod("installer_files/install.sh", 0o755)

    # Create package structure
    print("Creating package structure...")
    package_dir = f"TimeAttendanceSystem-{version}-Ubuntu"
    os.makedirs(package_dir, exist_ok=True)

    # Copy executable and assets to package
    shutil.copy("dist/TimeAttendanceSystem", package_dir)
    shutil.copytree("assets", f"{package_dir}/assets")
    shutil.copytree("dist/logs", f"{package_dir}/logs")
    shutil.copytree("dist/exports", f"{package_dir}/exports")
    shutil.copytree("dist/backup", f"{package_dir}/backup")
    shutil.copy("installer_files/install.sh", package_dir)
    shutil.copy("installer_files/timeattendancesystem.desktop", package_dir)
    shutil.copy("version.txt", package_dir)

    # Create README for Ubuntu
    with open(f"{package_dir}/README_UBUNTU.txt", "w") as f:
        f.write(f"""Time Attendance System v{version} for Ubuntu
=======================================

Installation:
1. Open a terminal in this directory
2. Run the installation script: sudo ./install.sh

After installation, you can:
- Launch from your applications menu
- Run from terminal: timeattendancesystem

The application will store data in ~/.config/TimeAttendanceSystem/
""")

    # Create tarball
    print("Creating tarball...")
    tarball_name = f"{package_dir}.tar.gz"
    subprocess.check_call(["tar", "czf", tarball_name, package_dir])

    print(f"Build completed: {tarball_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())