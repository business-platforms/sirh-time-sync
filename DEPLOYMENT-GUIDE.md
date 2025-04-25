# Time Attendance System: Deployment Guide

This document provides instructions for generating a deployable version of the Time Attendance System application for distribution to end-users.

## Prerequisites

Before building the application, ensure you have the following installed:

- **Python 3.9+** - The application requires Python 3.9 or newer
- **Git** - For version control and accessing the source code
- **Inno Setup 6+** - Required to build the Windows installer package
- **Windows OS** - The build process is designed for Windows environments

## Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/business-platforms/sirh-time-sync
   cd sirh-time-sync
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Inno Setup installation**
   
   Ensure Inno Setup is installed at one of these locations:
   - `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
   - `C:\Program Files\Inno Setup 6\ISCC.exe`

   If installed elsewhere, you'll need to modify the `ci_build.py` script to point to the correct location.

## Build Process

### Option 1: Using the CI Build Script (Recommended)

1. **Run the CI build script with the desired version number**
   ```bash
   python ci_build.py --version 1.0.0
   ```

   This script will:
   - Create the version file
   - Run PyInstaller to create the executable
   - Update the Inno Setup script with the version number
   - Run Inno Setup to create the installer
   - Copy the installer to the output location

2. **Locate the installer**
   
   After a successful build, the installer will be available at:
   - `installer/TimeAttendanceSystem-Setup-{version}.exe`
   - `installer/TimeAttendanceSystem-Setup-latest.exe` (copy of the latest version)

### Option 2: Manual Build Process

If you need more control over the build process, you can execute each step manually:

1. **Create version file**
   ```bash
   echo "1.0.0" > version.txt
   ```

2. **Run the build script to create the executable**
   ```bash
   python build.py
   ```

3. **Edit the Inno Setup script if needed**
   
   Open `TimeAttendanceSystem-Installer.iss` and update any parameters like the version number.

4. **Run Inno Setup Compiler**
   ```bash
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" TimeAttendanceSystem-Installer.iss
   ```

5. **Locate the installer in the `installer` directory**

## Customizing the Build

### Application Assets

- **Logo Files**: Place your logo files in the `assets` folder:
  - `assets/logo.png` - Company logo
  - `assets/timesync-logo.png` - Application logo
  - Ensure these are properly sized and formatted

### Update Server Configuration

Before distributing, configure the update server URL in `src/application.py`:

### Installer Customization

To customize the installer appearance and behavior, edit the `TimeAttendanceSystem-Installer.iss` file. You can modify:

- Company information
- License agreements
- Installation directory
- Start menu entries
- Desktop shortcuts
- Post-installation actions

## Deployment Options

### Standard Installation Package

The generated `.exe` installer is the primary deployment method. End-users simply run this file to install the application with all necessary components.

### Silent Installation

For automated deployments, the installer supports silent installation:

```
TimeAttendanceSystem-Setup-1.0.0.exe /VERYSILENT /NORESTART
```

### Update Server Setup

To enable automatic updates:

1. Host the installer files on a web server
2. Create a JSON API endpoint that returns update information in this format:
   ```json
   {
     "update_available": true,
     "version": "1.0.1",
     "download_url": "https://your-server.com/downloads/TimeAttendanceSystem-Setup-1.0.1.exe",
     "notes": "Bug fixes and performance improvements"
   }
   ```

## Troubleshooting Common Issues

### Missing Dependencies

If the build fails with missing dependencies, ensure you have installed all required packages:
```bash
pip install -r requirements.txt
```

### Inno Setup Not Found

If the build script cannot find Inno Setup, edit the `ci_build.py` file to specify the correct path to `ISCC.exe`.

### PyInstaller Errors

For PyInstaller-related errors:
1. Clear the `dist` and `build` directories
2. Check for any hidden imports that might be missing
3. Run PyInstaller with the `--debug` flag to get more information

### Database Migration Issues

When upgrading from a previous version:
- The application will automatically use the AppData location for new installations
- For upgrades, the installer will copy the existing database to the AppData location
- If issues persist, users may need to manually copy their database file