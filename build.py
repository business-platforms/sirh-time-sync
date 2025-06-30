import PyInstaller.__main__
import os
import shutil

# Application version - This should be updated for each build
VERSION = "1.0.0"

# Create version file in root directory for installer
with open("version.txt", "w") as f:
    f.write(VERSION)

print(f"Created version.txt with version: {VERSION}")

# Clean previous build
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

# Create assets directory if it doesn't exist
if not os.path.exists("assets"):
    os.makedirs("assets")

# Add placeholder logo files if they don't exist
if not os.path.exists("assets/logo.png"):
    # Create an empty file
    with open("assets/logo.png", "wb") as f:
        f.write(b'')

if not os.path.exists("assets/timesync-logo.png"):
    # Create an empty file
    with open("assets/timesync-logo.png", "wb") as f:
        f.write(b'')

# Ensure the util directory exists for our new paths.py module
os.makedirs("src/util", exist_ok=True)

# Define PyInstaller arguments with pandas/numpy fixes and psutil
args = [
    "main.py",
    "--name=timesync",
    "--onefile",
    "--windowed",
    "--add-data=assets;assets",
    "--add-data=src;src",
    "--add-data=version.txt;.",

    # Core hidden imports
    "--hidden-import=sqlite3",
    "--hidden-import=requests",
    "--hidden-import=zk",
    "--hidden-import=schedule",
    "--hidden-import=uuid",
    "--hidden-import=tkinter.simpledialog",
    "--hidden-import=pystray",
    "--hidden-import=PIL",
    "--hidden-import=psutil",  # Added for process management

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
    "--clean",  # Clean build cache
]

print("Starting PyInstaller build...")

# Run PyInstaller
PyInstaller.__main__.run(args)

# Create necessary directories in the distribution directory
os.makedirs("dist/logs", exist_ok=True)
os.makedirs("dist/exports", exist_ok=True)
os.makedirs("dist/backup", exist_ok=True)

# CRITICAL FIX: Copy version.txt to dist directory for installer to pick up
dist_version_path = "dist/version.txt"
if os.path.exists("version.txt"):
    shutil.copy2("version.txt", dist_version_path)
    print(f"Copied version.txt to {dist_version_path}")
else:
    # Create version file in dist if it doesn't exist
    with open(dist_version_path, "w") as f:
        f.write(VERSION)
    print(f"Created version.txt in dist directory: {dist_version_path}")

# Verify the version file was created
if os.path.exists(dist_version_path):
    with open(dist_version_path, "r") as f:
        created_version = f.read().strip()
    print(f"Verified version file in dist: {created_version}")
else:
    print("ERROR: Version file not found in dist directory!")

print(f"Build completed: timesync v{VERSION}")
print("Note: Database will be stored in user's AppData folder for persistence")
print(f"Version file created at: {dist_version_path}")

# Additional verification
executable_path = "dist/timesync.exe"
if os.path.exists(executable_path):
    print(f"Executable created: {executable_path}")
    print(f"Executable size: {os.path.getsize(executable_path) / 1024 / 1024:.2f} MB")
else:
    print("ERROR: Executable not found!")