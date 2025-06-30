# Time Attendance System - Upgrade Functionality Documentation

## Overview

The Time Attendance System includes an automated update mechanism that allows deployed applications to automatically check for, download, and install new versions. This system consists of three main components:

1. **Client Application** - Checks for updates and handles installation
2. **Update Server** - Manages versions and serves update files
3. **Build/Release Process** - Creates and deploys new versions

## System Architecture

### Update Server
- **Location**: `timesync-dev.rh-partner.com`
- **Port**: 3010
- **Technology**: Node.js with Express
- **Database**: SQLite for user authentication
- **File Storage**: `/usr/src/downloads` for installer files
- **Configuration Storage**: `/usr/src/app-data` for version metadata

### Client Update Process
- Applications automatically check for updates on startup
- Users can manually check via the configuration interface
- Updates are downloaded and installed with user consent
- Mandatory updates can be enforced for critical releases

## Release Management Process

### 1. Building a New Version

**Prerequisites:**
- Windows development environment
- Python 3.9+
- Inno Setup 6+
- Access to source code repository

**Steps:**
1. Update version number in desired format (e.g., 1.0.2)
2. Run the build command:
   ```bash
   python ci_build.py --version 1.0.2
   ```
3. Locate the generated installer:
   - `installer/timesync-setup-1.0.2.exe`
   - `installer/timesync-setup-latest.exe`

### 2. Deploying to Update Server

**File Upload:**
1. Copy the installer file to the server's download directory:
   ```
   sudo cp timesync-setup-X.X.X.exe /root/sirh/time-sync/downloads/timesync-setup-X.X.X.exe
   ```
2. execute these commands to change the ownership of the file: 
   ``` 
   sudo chmod 644 /root/sirh/time-sync/downloads/timesync-setup-X.X.X.exe
   ```

**Version Registration:**
1. Use the admin API to register the new version:
   ```http
   POST /api/admin/versions/add
   Headers: admin-key: [ADMIN_KEY]
   Body: {
     "version": "1.0.2",
     "notes": "Bug fixes and performance improvements"
   }
   ```

### 3. Verification
1. Check server health: `GET /health`
2. Test update check with a client application
3. Verify file download works correctly

## Server Administration

### Environment Variables
- `PORT`: Server port (default: 3010)
- `ADMIN_KEY`: Administrative access key
- `NODE_ENV`: Environment setting

### Database Management
**Location**: Server handles SQLite database automatically

**User Management:**
- Add new users (companies) via admin API:
  ```http
  POST /api/admin/users/add
  Headers: admin-key: [ADMIN_KEY]
  Body: {
    "email": "company@domain.com",
    "secret_key": "their-secret-key"
  }
  ```

### File Management
**Installer Files:**
- Store in `/usr/src/downloads/`
- Follow naming convention: `timesync-setup-{version}.exe`
- Files are automatically checksummed on server startup

**Version Metadata:**
- Stored in `/usr/src/app-data/versions.json`
- Managed automatically via API
- Contains version history and release notes

### Monitoring
**Health Check:**
- Endpoint: `GET /health`
- Returns server status, uptime, and memory usage

**Logs:**
- Server logs all operations with detailed timestamps
- Monitor for authentication failures and download errors

## Client Configuration

### Update Server Settings
Clients must be configured with:
- Company email address
- Secret key for authentication
- Update server URL (configured in application)

### Update Behavior
- **Automatic checks**: On application startup
- **Manual checks**: Via configuration interface
- **Mandatory updates**: Can be enforced for critical releases
- **Silent installation**: Updates install automatically after download


## Security Considerations

### Access Control
- Admin operations require admin key authentication
- User operations require email/secret key pairs
- Download tokens expire after 10 minutes
- Tokens are single-use only

### File Integrity
- All installer files are checksummed (SHA-256)
- Clients verify checksums before installation
- Corrupted downloads are automatically rejected

### Network Security
- HTTPS should be used in production
- Security headers are automatically applied
- Rate limiting should be considered for production use

## API Reference

### Update Check Endpoint
```http
GET /api/updates/check?version=1.0.0
Headers:
  email: company@domain.com
  secret-key: their-secret-key

Response:
{
  "update_available": true,
  "version": "1.0.2",
  "download_token": "abc123...",
  "download_url": "http://server/api/updates/download?token=abc123...",
  "notes": "Release notes",
  "expires_in": 600
}
```

### Download Endpoint
```http
GET /api/updates/download?token=abc123...

Response: Binary installer file
Headers:
  Content-Type: application/octet-stream
  Content-Disposition: attachment; filename="timesync-setup-1.0.2.exe"
  X-Content-Checksum: sha256-hash
  X-Checksum-Algorithm: sha256
```

### Admin - Add Version
```http
POST /api/admin/versions/add
Headers:
  admin-key: admin-secret-key
Body:
{
  "version": "1.0.2",
  "notes": "Release notes"
}
```

### Admin - Add User
```http
POST /api/admin/users/add
Headers:
  admin-key: admin-secret-key
Body:
{
  "email": "company@domain.com",
  "secret_key": "their-secret-key"
}
```

### Health Check
```http
GET /health

Response:
{
  "status": "OK",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "uptime_seconds": 3600,
  "uptime_readable": "1h 0m 0s",
  "memory_usage_mb": {
    "rss": "50.25",
    "heapTotal": "30.50",
    "heapUsed": "25.75",
    "external": "5.25"
  },
  "node_env": "production"
}
```

## File Structure

### Server Directory Structure
```
/usr/src/
├── app-data/
│   └── versions.json          # Version metadata
├── downloads/
│   ├── timesync-setup-1.0.0.exe
│   ├── timesync-setup-1.0.1.exe
│   └── timesync-setup-1.0.2.exe
└── app/
    ├── server.js              # Main server file
    ├── db.js                  # Database operations
    └── package.json
```

### Client Directory Structure
```
Application/
├── timesync.exe               # Main application
├── version.txt                # Current version
├── src/
│   ├── update_checker.py      # Update functionality
│   └── application.py         # Main application logic
└── logs/
    └── attendance_system_*.log
```
