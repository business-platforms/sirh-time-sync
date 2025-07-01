# Time Attendance System Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [System Overview](#system-overview)
3. [Installation and Setup](#installation-and-setup)
4. [User Interface](#user-interface)
5. [Configuration](#configuration)
6. [Features and Functionality](#features-and-functionality)
7. [System Architecture](#system-architecture)
8. [Troubleshooting](#troubleshooting)
9. [Appendices](#appendices)

## Introduction

The Time Attendance System is a desktop application designed to automate the collection, management, and synchronization of employee attendance data. It connects to biometric devices for collecting attendance records, provides interfaces for managing users and records, and synchronizes this data with RHP for further processing.

### Key Features

- Integration with biometric attendance devices (ZK devices)
- Automated collection of attendance records at configurable intervals
- User management with import capabilities
- Record management with error handling
- API synchronization of attendance data
- System tray integration for background operation
- Automatic update checking and installation

## System Overview

The Time Attendance System creates a bridge between physical attendance devices and RHP. It operates by:

1. **Collecting attendance data** from the biometric device at regular intervals
2. **Storing collected data** in a local database for reliability
3. **Processing and validating** the attendance records 
4. **Uploading attendance data** to the central HR system via API
5. **Importing employee information** from the API to the device

The application runs as a Windows desktop application with a user interface for configuration and management, and can also run in the background through the system tray.

## Installation and Setup

### System Requirements

- Windows 10 or newer
- .NET Framework 4.6.1 or newer
- 2GB RAM minimum (4GB recommended)
- 100MB available disk space
- Network connectivity to both the biometric device and the internet

### Installation Steps

- Refer to DEPLOYMENT-GUIDE.md for installation instructions

### First-Time Setup

1. Launch the application from the desktop shortcut or start menu
2. The configuration interface will open automatically on first run
3. Enter the following required information:
   - Company ID
   - API Username and Password
   - Device IP address and port
   - Collection, upload, and import intervals
4. Test the device and API connections
5. Save the configuration

## User Interface

The application features a modern, intuitive user interface with several key sections:

### Main Window

The main window consists of:

- **System Controls**: Start/stop buttons to manage the attendance collection service
- **Connection Tests**: Test device and API connectivity
- **System Information**: Status of collectors and recent activities
- **Navigation Buttons**: Access to configuration, users, and records interfaces

### Configuration Interface

The configuration interface allows you to:

- Set company and API credentials
- Configure device connection parameters
- Adjust collection, upload, and import intervals
- Test device and API connectivity

### Users Interface

The users interface enables you to:

- View all users stored on the device
- Import users from the API
- Refresh the user list

### Records Interface

The records interface provides functionality to:

- View all attendance records with filtering options
- Add, edit, and delete records
- Mark records as processed or unprocessed
- View and manage record errors
- Synchronize records with the API

### System Tray Integration

The application can be minimized to the system tray, allowing it to:

- Run in the background while collecting attendance data
- Provide quick access to start/stop the service
- Show notifications for important events

## Configuration

### API Configuration

- **Company ID**: Your organization's unique identifier
- **API Username**: Account username for API authentication
- **API Password**: Account password for API authentication

### Device Configuration

- **Device IP**: IP address of the biometric device
- **Device Port**: Network port for the device (default: 4370)

### Scheduler Configuration

- **Collection Interval**: How often to collect attendance records (minutes)
- **Upload Interval**: How often to upload records to API (minutes)
- **User Import Interval**: How often to import users from API (minutes)

## Features and Functionality

### Attendance Collection

The system automatically collects attendance records from the connected biometric device at specified intervals. This includes:

- Retrieving new records from the device
- Storing records in the local database
- Associating records with appropriate user information

### User Management

User management features include:

- Viewing all users in the system
- Importing users from the API to the device
- Real-time refreshing of user data

### Record Management

The records interface provides comprehensive tools for managing attendance data:

- **Filtering**: Filter records by status (processed, unprocessed, error)
- **Searching**: Search records by user code or timestamp
- **Editing**: Add, update, or delete attendance records
- **Status Management**: Mark records as processed or unprocessed
- **Error Handling**: View and manage record errors

### API Synchronization

The system synchronizes data with the central API in two ways:

- **Uploading Attendance Records**: Sends collected attendance data to the API
- **Importing Users**: Downloads user information from the API to update the device

### Automated Scheduling

The scheduler service manages recurring tasks:

- **Attendance Collection**: Collects attendance records at specified intervals
- **Record Upload**: Uploads unprocessed records to the API at specified intervals
- **User Import**: Imports users from the API at specified intervals

### Update Management

The application includes an update checker that:

- Periodically checks for new versions
- Notifies users when updates are available
- Handles downloading and installing updates

## System Architecture

The Time Attendance System is built with a modular architecture consisting of:

### Core Components

- **Dependency Container**: Manages service dependencies
- **Application Manager**: Coordinates system operation
- **Database Management**: Handles SQLite database operations

### Services

- **Device Service**: Communicates with the biometric device
- **API Service**: Manages API communication
- **Attendance Service**: Handles attendance record operations
- **Sync Service**: Orchestrates synchronization between device and API
- **Scheduler Service**: Manages scheduled tasks

### Data Storage

The system uses a SQLite database stored in the user's AppData folder with tables for:

- **Configuration**: System configuration settings
- **Attendance Records**: Collected attendance data
- **API Upload Logs**: Records of API synchronization attempts

## Troubleshooting

### Connection Issues

#### Device Connection Failures
- Verify the device IP address and port in the configuration
- Ensure the device is powered on and connected to the network
- Check that no firewalls are blocking the connection
- Try restarting the device

#### API Connection Failures
- Verify your company ID, username, and password
- Check internet connectivity
- Ensure API endpoints are accessible from your network

### Data Synchronization Issues

#### Record Upload Failures
- Check the API connection settings
- Review error details in the records interface
- Verify that records are in the correct format
- Check API upload logs for specific error messages

#### User Import Failures
- Verify API credentials
- Check that users exist in the central system
- Review system logs for detailed error information

### Application Issues

#### Application Won't Start
- Check Windows Event Viewer for error logs
- Verify that the database file is not corrupted
- Ensure all dependencies are properly installed

#### Service Won't Run
- Check configuration settings
- Verify device and API connectivity
- Review application logs for error details

### Logging

The application creates detailed logs in the `logs` directory:
- Log files use the naming pattern: `attendance_system_YYYYMMDD_HHMMSS.log`
- Review these logs for detailed information about system operations and errors

## Appendices

### Data Models

#### User
- `user_id`: Unique identifier
- `name`: User name (employee code)
- `code`: Additional employee code (if applicable)

#### Attendance Record
- `id`: Record identifier
- `user_id`: User identifier
- `username`: User name
- `timestamp`: Date and time of attendance event
- `punch_type`: Type of punch (IN or OUT)
- `processed`: Processing status (UNPROCESSED, PROCESSED, ERROR)
- `errors`: Error information (if applicable)

### Error Codes

| Code | Description |
|------|-------------|
| E311 | Month pointing already exists |
| E312 | Hours and days must be null |
| E314 | Maximum days exceeded |
| E315 | Maximum hours exceeded |
| E316 | Pointing day greater than exit day |
| E322 | Invalid pointing interval |
| E323 | Pointing overlap |
| E344 | Pointing day less than start day |
| E360 | No corresponding entrance |

### Command Line Options

The application can be run with the following command line options: 

- `--config`: Open only the configuration interface
- `--start`: Start the collection service in command line mode
- `--stop`: Stop the collection service
