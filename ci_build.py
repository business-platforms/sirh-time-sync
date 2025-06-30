import PyInstaller.__main__
import os
import sys
import shutil
import subprocess
import argparse
import platform
from datetime import datetime


def main():
    """Main entry point for the attendance system build."""
    parser = argparse.ArgumentParser(description='Build the Time Attendance System application')
    parser.add_argument('--version', required=True, help='Version number (e.g., 1.0.0)')
    parser.add_argument('--installer', choices=['inno', 'nsis'], default='auto',
                        help='Installer type: inno (Windows), nsis (Linux), or auto (detect)')
    args = parser.parse_args()

    version = args.version
    installer_type = detect_installer_type(args.installer)

    print(f"Building Time Attendance System v{version}")
    print(f"Platform: {platform.system()}")
    print(f"Using installer: {installer_type}")

    # Create version file
    with open("version.txt", "w") as f:
        f.write(version)

    # Run PyInstaller build
    print("Running PyInstaller...")
    run_pyinstaller_build()

    # Run appropriate installer
    if installer_type == 'inno':
        print("Running Inno Setup...")
        run_inno_setup_build(version)
    elif installer_type == 'nsis':
        print("Running NSIS...")
        run_nsis_build(version)
    else:
        print("Error: No suitable installer found")
        return 1

    print(f"Build completed: timesync v{version}")
    return 0


def detect_installer_type(installer_arg):
    """Detect which installer to use based on system and argument."""
    if installer_arg == 'inno':
        return 'inno'
    elif installer_arg == 'nsis':
        return 'nsis'
    elif installer_arg == 'auto':
        # Auto-detect based on platform and available tools
        system = platform.system()

        if system == 'Windows':
            # On Windows, prefer Inno Setup
            if shutil.which('iscc') or os.path.exists("C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"):
                return 'inno'
            elif shutil.which('makensis'):
                return 'nsis'
        else:
            # On Linux/macOS, prefer NSIS
            if shutil.which('makensis'):
                return 'nsis'
            elif shutil.which('iscc'):  # Unlikely but possible
                return 'inno'

        print("Error: Neither NSIS nor Inno Setup found")
        return None


def run_pyinstaller_build():
    """Run PyInstaller to create the executable."""
    # Clean previous build
    clean_build_directories()

    # Create assets directory if it doesn't exist
    if not os.path.exists("assets"):
        os.makedirs("assets")

    # Add placeholder logo files if they don't exist
    create_placeholder_assets()

    # Detect platform for correct separator
    is_windows = platform.system() == 'Windows'
    separator = ';' if is_windows else ':'

    # PyInstaller arguments with platform-aware separators
    args = [
        "main.py",
        "--name=timesync",
        "--onefile",
        "--windowed",
        f"--add-data=assets{separator}assets",
        f"--add-data=src{separator}src",
        f"--add-data=version.txt{separator}.",

        # Core hidden imports
        "--hidden-import=sqlite3",
        "--hidden-import=requests",
        "--hidden-import=zk",
        "--hidden-import=schedule",
        "--hidden-import=uuid",
        "--hidden-import=tkinter.simpledialog",
        "--hidden-import=pystray",
        "--hidden-import=PIL",
        "--hidden-import=psutil",

        # Pandas and numpy specific fixes
        "--hidden-import=pandas",
        "--hidden-import=pandas._libs.tslibs.timedeltas",
        "--hidden-import=pandas._libs.tslibs.np_datetime",
        "--hidden-import=pandas._libs.tslibs.nattype",
        "--hidden-import=pandas._libs.skiplist",
        "--hidden-import=pandas.io.formats.style",
        "--hidden-import=numpy",
        "--hidden-import=numpy.random.common",
        "--hidden-import=numpy.random.bounded_integers",
        "--hidden-import=numpy.random.entropy",

        # Openpyxl for Excel functionality
        "--hidden-import=openpyxl",
        "--hidden-import=openpyxl.workbook",
        "--hidden-import=openpyxl.worksheet.worksheet",

        # Additional fixes for pandas dependencies
        "--collect-submodules=pandas",
        "--collect-submodules=numpy",
        "--collect-data=pandas",

        # Exclude problematic modules to reduce size
        "--exclude-module=matplotlib",
        "--exclude-module=scipy",
        "--exclude-module=IPython",
        "--exclude-module=jupyter",
        "--exclude-module=notebook",
        "--exclude-module=tkinter.test",

        # Build configuration
        "--distpath=./dist",
        "--workpath=./build",
        "--clean",
    ]

    # Run PyInstaller
    PyInstaller.__main__.run(args)

    # Create necessary directories in dist
    create_dist_directories()


def clean_build_directories():
    """Clean previous build directories using platform-appropriate commands."""
    directories = ["dist", "build", "installer"]

    for directory in directories:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"Cleaned {directory}/")
            except Exception as e:
                print(f"Warning: Could not clean {directory}/: {e}")


def create_dist_directories():
    """Create necessary directories in the distribution."""
    directories = ["dist/logs", "dist/exports", "dist/backup"]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created {directory}/")


def run_inno_setup_build(version):
    """Run Inno Setup to create the installer."""
    # Update version in Inno Setup script
    update_inno_version(version)

    # Create installer directory
    os.makedirs("installer", exist_ok=True)

    # Run Inno Setup compiler
    inno_script = os.path.abspath("timesync-installer.iss")

    # Try different possible paths for ISCC
    iscc_paths = [
        "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
        "C:\\Program Files\\Inno Setup 6\\ISCC.exe",
        "iscc"  # If in PATH
    ]

    iscc_path = None
    for path in iscc_paths:
        if os.path.exists(path) or shutil.which(path):
            iscc_path = path
            break

    if not iscc_path:
        raise Exception("Inno Setup Compiler (ISCC.exe) not found")

    print(f"Using Inno Setup compiler: {iscc_path}")
    subprocess.check_call([iscc_path, inno_script])


def run_nsis_build(version):
    """Run NSIS to create the installer."""
    # Update version in NSIS script
    update_nsis_version(version)

    # Create installer directory
    os.makedirs("installer", exist_ok=True)

    # Run NSIS compiler
    nsis_script = os.path.abspath("timesync-installer.nsi")

    # Check if makensis is available
    makensis_path = shutil.which('makensis')
    if not makensis_path:
        raise Exception("NSIS compiler (makensis) not found. Install with: sudo apt install nsis")

    print(f"Using NSIS compiler: {makensis_path}")
    print(f"Building installer from: {nsis_script}")

    # Run makensis with verbose output
    result = subprocess.run(["makensis", "-V2", nsis_script],
                            capture_output=True, text=True)

    if result.returncode != 0:
        print("NSIS build failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        raise Exception(f"NSIS build failed with code {result.returncode}")
    else:
        print("NSIS build successful!")
        print(result.stdout)


def update_inno_version(version):
    """Update version in Inno Setup script."""
    script_path = "timesync-installer.iss"
    if not os.path.exists(script_path):
        print(f"Warning: {script_path} not found")
        return

    with open(script_path, "r", encoding='utf-8') as f:
        content = f.read()

    # Replace version line
    content = content.replace(
        '#define AppVersion "1.0.1"',
        f'#define AppVersion "{version}"'
    )

    with open(script_path, "w", encoding='utf-8') as f:
        f.write(content)

    print(f"Updated Inno Setup script version to {version}")


def update_nsis_version(version):
    """Update version in NSIS script."""
    script_path = "timesync-installer.nsi"
    if not os.path.exists(script_path):
        print(f"Warning: {script_path} not found")
        return

    with open(script_path, "r", encoding='utf-8') as f:
        content = f.read()

    # Replace version line
    content = content.replace(
        '!define APP_VERSION "1.0.1"',
        f'!define APP_VERSION "{version}"'
    )

    with open(script_path, "w", encoding='utf-8') as f:
        f.write(content)

    print(f"Updated NSIS script version to {version}")


def create_placeholder_assets():
    """Create placeholder asset files if they don't exist."""
    assets = [
        "assets/logo.png",
        "assets/timesync-logo.png",
        "assets/timesync-logo.ico"
    ]

    for asset in assets:
        if not os.path.exists(asset):
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(asset), exist_ok=True)

            # Create empty placeholder file
            with open(asset, "wb") as f:
                f.write(b'')  # Empty placeholder
            print(f"Created placeholder: {asset}")


if __name__ == "__main__":
    sys.exit(main() or 0)