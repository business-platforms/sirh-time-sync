# ci_build.py
import os
import sys
import subprocess
import shutil
import argparse
from datetime import datetime


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Build the Time Attendance System application')
    parser.add_argument('--version', required=True, help='Version number (e.g., 1.0.0)')
    args = parser.parse_args()

    version = args.version
    print(f"Building Time Attendance System v{version}")

    # Create version file
    with open("version.txt", "w") as f:
        f.write(version)

    # Run PyInstaller build
    print("Running PyInstaller...")
    subprocess.check_call([sys.executable, "build.py"])

    # Run Inno Setup
    print("Running Inno Setup...")
    inno_script = os.path.abspath("TimeAttendanceSystem-Installer.iss")

    # Update version in Inno Setup script
    with open(inno_script, "r") as f:
        script_content = f.read()

    script_content = script_content.replace(
        '#define AppVersion "1.0.0"',
        f'#define AppVersion "{version}"'
    )

    with open(inno_script, "w") as f:
        f.write(script_content)

    # Run Inno Setup compiler
    iscc_path = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
    if not os.path.exists(iscc_path):
        # Try alternate path
        iscc_path = "C:\\Program Files\\Inno Setup 6\\ISCC.exe"
        if not os.path.exists(iscc_path):
            print("Error: Could not find Inno Setup Compiler (ISCC.exe)")
            return 1

    subprocess.check_call([iscc_path, inno_script])

    # Copy installer to versioned file and latest version
    installer_path = os.path.join("installer", f"TimeAttendanceSystem-Setup-{version}.exe")
    latest_path = os.path.join("installer", "TimeAttendanceSystem-Setup-latest.exe")

    if os.path.exists(installer_path):
        shutil.copy2(installer_path, latest_path)
        print(f"Build completed: {installer_path}")
        return 0
    else:
        print(f"Error: Installer not found at {installer_path}")
        return 1


if __name__ == "__main__":
    sys.exit(main())