import os
import sys
import subprocess
import shutil
import argparse
from datetime import datetime


def update_build_script_version(version):
    """Update the version in build.py"""
    build_script_path = "build.py"

    if os.path.exists(build_script_path):
        with open(build_script_path, "r") as f:
            content = f.read()

        # Replace the VERSION line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('VERSION = '):
                lines[i] = f'VERSION = "{version}"'
                break

        with open(build_script_path, "w") as f:
            f.write('\n'.join(lines))

        print(f"Updated build.py with version {version}")
    else:
        print(f"Warning: {build_script_path} not found")


def update_installer_version(version):
    """Update the version in the Inno Setup script"""
    inno_script = "timesync-installer.iss"

    if os.path.exists(inno_script):
        with open(inno_script, "r") as f:
            script_content = f.read()

        # Update version in Inno Setup script
        script_content = script_content.replace(
            '#define AppVersion "1.0.1"',
            f'#define AppVersion "{version}"'
        )

        with open(inno_script, "w") as f:
            f.write(script_content)

        print(f"Updated {inno_script} with version {version}")
    else:
        print(f"Warning: {inno_script} not found")


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Build the Time Attendance System application')
    parser.add_argument('--version', required=True, help='Version number (e.g., 1.0.0)')
    args = parser.parse_args()

    version = args.version
    print(f"Building Time Attendance System v{version}")

    # Update version in build script
    update_build_script_version(version)

    # Update version in installer script
    update_installer_version(version)

    # Create version file in root directory (will be used by build.py)
    with open("version.txt", "w") as f:
        f.write(version)
    print(f"Created root version.txt with version {version}")

    # Run PyInstaller build
    print("Running PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "build.py"])
        print("PyInstaller build completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller build failed: {e}")
        return 1

    # Verify that all necessary files exist before running Inno Setup
    required_files = [
        "dist/timesync.exe",
        "dist/version.txt",
        "version.txt"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"Error: Missing required files: {missing_files}")
        return 1

    print("All required files present, proceeding with installer creation...")

    # Run Inno Setup
    print("Running Inno Setup...")
    inno_script = os.path.abspath("timesync-installer.iss")

    # Run Inno Setup compiler
    iscc_path = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
    if not os.path.exists(iscc_path):
        # Try alternate path
        iscc_path = "C:\\Program Files\\Inno Setup 6\\ISCC.exe"
        if not os.path.exists(iscc_path):
            print("Error: Could not find Inno Setup Compiler (ISCC.exe)")
            return 1

    try:
        subprocess.check_call([iscc_path, inno_script])
        print("Inno Setup completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Inno Setup failed: {e}")
        return 1

    # Copy installer to versioned file and latest version
    installer_path = os.path.join("installer", f"timesync-setup-{version}.exe")
    latest_path = os.path.join("installer", "timesync-setup-latest.exe")

    if os.path.exists(installer_path):
        shutil.copy2(installer_path, latest_path)

        # Verify installer file size
        installer_size = os.path.getsize(installer_path) / 1024 / 1024
        print(f"Build completed: {installer_path} ({installer_size:.2f} MB)")
        print(f"Latest installer: {latest_path}")

        # Additional verification
        print("\nBuild Verification:")
        print(f"✓ Executable: dist/timesync.exe")
        print(f"✓ Version file (dist): dist/version.txt")
        print(f"✓ Version file (root): version.txt")
        print(f"✓ Installer: {installer_path}")

        return 0
    else:
        print(f"Error: Installer not found at {installer_path}")
        return 1


if __name__ == "__main__":
    sys.exit(main())