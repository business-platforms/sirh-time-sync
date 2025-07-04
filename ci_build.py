import os
import sys
import subprocess
import shutil
import argparse
import json
from datetime import datetime


def safe_print(message):
    """Print message safely, handling encoding issues."""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback: remove non-ASCII characters
        ascii_message = message.encode('ascii', 'ignore').decode('ascii')
        print(ascii_message)


def load_profile_config(profile_name):
    """Load profile configuration from JSON file."""
    # Map short names to full names for file lookup
    profile_mapping = {
        'dev': 'dev',
        'staging': 'staging',
        'prod': 'prod',
    }

    full_profile_name = profile_mapping.get(profile_name, profile_name)
    profile_path = f"profiles/{full_profile_name}.json"

    if not os.path.exists(profile_path):
        safe_print(f"Profile not found: {profile_path}")
        safe_print("Using production defaults")
        return get_production_profile()

    with open(profile_path, "r", encoding='utf-8') as f:
        return json.load(f)


def get_production_profile():
    """Get production profile as fallback."""
    return {
        "environment": "prod",
        "api_url": "https://app.rh-partner.com",
        "update_server_url": "https://timesync.rh-partner.com/api/updates",
        "database_suffix": "",
        "ui_config": {
            "header_color": "#24398E",
            "environment_badge": None,
            "show_environment_indicator": False,
            "window_title_suffix": ""
        }
    }


def embed_profile_in_build(profile_config, version, profile_name):
    """Embed profile configuration into the build."""
    # Create embedded configuration
    embedded_config = {
        "profile": profile_config,
        "version": version,
        "profile_name": profile_name,
        "build_timestamp": datetime.now().isoformat(),
        "build_environment": profile_config["environment"]
    }

    # Ensure src directory exists
    os.makedirs("src", exist_ok=True)

    # Write embedded profile for PyInstaller to include
    embedded_path = "src/embedded_profile.json"
    with open(embedded_path, "w", encoding='utf-8') as f:
        json.dump(embedded_config, f, indent=2)

    safe_print(f"[OK] Embedded profile: {profile_config['environment']} -> {embedded_path}")
    return embedded_path


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

        safe_print(f"[OK] Updated build.py with version {version}")
    else:
        safe_print(f"[WARNING] {build_script_path} not found")


def update_installer_version(version, profile_name):
    """Update the version in the Inno Setup script."""
    inno_script = "timesync-installer.iss"

    if os.path.exists(inno_script):
        with open(inno_script, "r", encoding='utf-8') as f:
            script_content = f.read()

        # Update version in Inno Setup script
        script_content = script_content.replace(
            '#define AppVersion "1.0.1"',
            f'#define AppVersion "{version}"'
        )

        # Update app name for non-production environments
        if profile_name not in ['prod', 'prod']:
            env_name = profile_name.upper()
            script_content = script_content.replace(
                '#define MyAppName "Time Attendance System"',
                f'#define MyAppName "Time Attendance System [{env_name}]"'
            )

            # Update output filename
            script_content = script_content.replace(
                'OutputBaseFilename=timesync-setup-{#AppVersion}',
                f'OutputBaseFilename=timesync-setup-{profile_name}-{{#AppVersion}}'
            )

        with open(inno_script, "w", encoding='utf-8') as f:
            f.write(script_content)

        safe_print(f"[OK] Updated {inno_script} for {profile_name} environment")
    else:
        safe_print(f"[WARNING] {inno_script} not found")


def main():
    parser = argparse.ArgumentParser(description='Build the Time Attendance System application')
    parser.add_argument('--version', required=True, help='Version number (e.g., 1.0.0)')
    parser.add_argument('--profile', default='dev',
                        choices=['dev', 'staging', 'prod'],
                        help='Environment profile to build for (default: dev)')
    args = parser.parse_args()

    version = args.version
    profile_name = args.profile

    safe_print("Building Time Attendance System")
    safe_print(f"Version: {version}")
    safe_print(f"Profile: {profile_name}")
    safe_print(f"Build Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print("-" * 50)

    try:
        safe_print(f"Loading profile configuration: {profile_name}")
        profile_config = load_profile_config(profile_name)
        safe_print(f"Environment: {profile_config['environment']}")
        safe_print(f"API URL: {profile_config['api_url']}")
        safe_print(f"Update Server: {profile_config['update_server_url']}")

        embed_profile_in_build(profile_config, version, profile_name)

    except Exception as e:
        safe_print(f"Error loading profile: {e}")
        return 1

    update_build_script_version(version)
    update_installer_version(version, profile_name)

    with open("version.txt", "w") as f:
        f.write(version)
    safe_print(f"[OK] Created root version.txt with version {version}")

    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    os.makedirs("dist", exist_ok=True)
    os.makedirs("installer_files", exist_ok=True)

    safe_print("Running PyInstaller...")

    try:
        subprocess.check_call([sys.executable, "build.py"])
        safe_print("[OK] PyInstaller build completed successfully")
    except subprocess.CalledProcessError as e:
        safe_print(f"[ERROR] PyInstaller build failed: {e}")
        return 1

    required_files = [
        "dist/timesync.exe",
        "dist/version.txt",
        "version.txt",
        "src/embedded_profile.json"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        safe_print(f"[ERROR] Missing required files: {missing_files}")
        return 1

    safe_print("[OK] All required files present, proceeding with installer creation...")

    safe_print("Running Inno Setup...")
    inno_script = os.path.abspath("timesync-installer.iss")

    iscc_path = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
    if not os.path.exists(iscc_path):
        iscc_path = "C:\\Program Files\\Inno Setup 6\\ISCC.exe"
        if not os.path.exists(iscc_path):
            safe_print("[ERROR] Could not find Inno Setup Compiler (ISCC.exe)")
            return 1

    try:
        subprocess.check_call([iscc_path, inno_script])
        safe_print("[OK] Inno Setup completed successfully")
    except subprocess.CalledProcessError as e:
        safe_print(f"[ERROR] Inno Setup failed: {e}")
        return 1

    # Determine installer name based on profile
    if profile_name in ['prod', 'prod']:
        installer_name = f"timesync-setup-{version}.exe"
        latest_name = "timesync-setup-latest.exe"
    else:
        installer_name = f"timesync-setup-{profile_name}-{version}.exe"
        latest_name = f"timesync-setup-{profile_name}-latest.exe"

    installer_path = os.path.join("installer", installer_name)
    latest_path = os.path.join("installer", latest_name)

    if os.path.exists(installer_path):
        shutil.copy2(installer_path, latest_path)

        installer_size = os.path.getsize(installer_path) / 1024 / 1024

        safe_print("=" * 50)
        safe_print("BUILD COMPLETED SUCCESSFULLY")
        safe_print("=" * 50)
        safe_print(f"Installer: {installer_name} ({installer_size:.2f} MB)")
        safe_print(f"Latest Copy: {latest_name}")
        safe_print(f"Environment: {profile_config['environment']}")
        safe_print(f"API URL: {profile_config['api_url']}")
        safe_print(f"Update Server: {profile_config['update_server_url']}")
        safe_print(f"Database Suffix: '{profile_config.get('database_suffix', '')}'")

        return 0
    else:
        safe_print(f"[ERROR] Installer not found at {installer_path}")
        return 1


if __name__ == "__main__":
    sys.exit(main())