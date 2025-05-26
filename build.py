# build.py
import PyInstaller.__main__
import os
import shutil

# Application version
VERSION = "1.0.0"

# Create version file
with open("version.txt", "w") as f:
    f.write(VERSION)

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

# Define PyInstaller arguments
# Define PyInstaller arguments with pandas/numpy fixes
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
# Run PyInstaller
PyInstaller.__main__.run(args)

# Create necessary directories in the distribution directory
# Note: We still create 'logs' and 'exports' which may be used with absolute paths
os.makedirs("dist/logs", exist_ok=True)
os.makedirs("dist/exports", exist_ok=True)
os.makedirs("dist/backup", exist_ok=True)

# We no longer create a placeholder database in the dist directory
# since our database will now be stored in the user's AppData folder

print(f"Build completed: timesync v{VERSION}")
print("Note: Database will be stored in user's AppData folder for persistence")