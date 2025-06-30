; Time Attendance System - Inno Setup Script
; This script handles installation, updates, and ensures single installation

#define MyAppName "Time Attendance System"
#define MyAppPublisher "Business Platforms"
#define MyAppURL "https://busniess-platforms.com"
#define MyAppExeName "timesync.exe"
#define AppVersion "1.0.1"

[Setup]
; Basic application information
AppId={{A1B2C3D4-E5F6-4A5B-8C7D-9E0F1A2B3C4D}}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppVerName={#MyAppName} {#AppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/support
AppUpdatesURL={#MyAppURL}/updates

; Installation paths and defaults
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=timesync-setup-{#AppVersion}

; Compression settings
Compression=lzma2
SolidCompression=yes

; Appearance and behavior
WizardStyle=modern
WizardResizable=no
SetupIconFile=assets\timesync-logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; Windows specific settings
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64

; Always create new log file
SetupLogging=yes

; Close applications and handle updates better
CloseApplications=force
RestartApplications=yes
AppMutex=TimeSyncMutex

; Update-specific settings
AllowUNCPath=false
DisableWelcomePage=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startupicon"; Description: "Lancer au démarrage de Windows"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\timesync.exe"; DestDir: "{app}"; Flags: ignoreversion replacesameversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs replacesameversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon
Name: "{commonstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up files that may be left behind
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\exports\*.*"
Type: files; Name: "{app}\logs\*.*"
Type: dirifempty; Name: "{app}\exports"
Type: dirifempty; Name: "{app}\logs"
Type: dirifempty; Name: "{app}"

; Note: We don't delete the database files in AppData as they should be preserved

[Registry]
; Add registry entries for uninstallation and automatic updates
Root: HKLM; Subkey: "Software\{#MyAppName}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKLM; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"

[Code]
var
  PreviousInstallPath: String;
  InstallationStartTime: String;

function IsApplicationRunning(): Boolean;
var
  FWnd: HWND;
begin
  FWnd := FindWindowByWindowName('Time Attendance System');
  if FWnd = 0 then
    FWnd := FindWindowByWindowName('Panneau de Contrôle du Système de Présence');
  Result := FWnd <> 0;
end;

function KillTask(TaskName: String): Integer;
var
  ResultCode: Integer;
begin
  Exec('taskkill.exe', '/f /im ' + TaskName, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := ResultCode;
end;

function InitializeSetup(): Boolean;
var
  UninstallString: String;
  ResultCode: Integer;
  TempDir: String;
  UpdatePendingFile: String;
  RetryCount: Integer;
begin
  Result := True;

  // Record installation start time
  InstallationStartTime := GetDateTimeString('yyyy-mm-dd hh:nn:ss', #0, #0);

  // Check for update pending file and clean it up
  TempDir := GetTempDir();
  UpdatePendingFile := TempDir + 'timesync_update_pending';
  if FileExists(UpdatePendingFile) then
  begin
    Log('Found update pending file, proceeding with installation');
  end;

  // Force close running application instances
  RetryCount := 0;
  while IsApplicationRunning() and (RetryCount < 5) do
  begin
    Log('Application is running, attempting to close it (attempt ' + IntToStr(RetryCount + 1) + ')');

    // Try to close gracefully first
    KillTask('timesync.exe');

    Sleep(2000); // Wait 2 seconds

    if IsApplicationRunning() then
    begin
      Log('Application still running after graceful close attempt');
      // Force kill if still running
      KillTask('timesync.exe');
      Sleep(1000);
    end;

    RetryCount := RetryCount + 1;
  end;

  if IsApplicationRunning() then
  begin
    Log('Warning: Could not close all application instances');
  end else
  begin
    Log('All application instances closed successfully');
  end;

  // Try to get the uninstaller path of the existing installation
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1',
                         'UninstallString', UninstallString) or
     RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1',
                         'UninstallString', UninstallString) then
  begin
    // Store previous installation path for backup purposes
    if RegQueryStringValue(HKLM, 'Software\{#MyAppName}', 'InstallPath', PreviousInstallPath) then
    begin
      Log('Previous installation found at: ' + PreviousInstallPath);
    end;

    // Previous installation exists - uninstall it silently without prompting
    if UninstallString <> '' then
    begin
      Log('Uninstalling previous version silently');
      // Add /SILENT to the uninstaller command
      UninstallString := RemoveQuotes(UninstallString);
      if Exec(UninstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      begin
        Log('Previous version uninstalled successfully');
      end
      else
      begin
        Log('Failed to uninstall previous version, return code: ' + IntToStr(ResultCode));
        // Continue anyway, as the installation might still work
      end;

      // Wait a moment to ensure uninstall completes
      Sleep(3000);
    end;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  RetryCount: Integer;
begin
  Result := '';
  NeedsRestart := False;

  // Final check and force close any remaining instances
  RetryCount := 0;
  while IsApplicationRunning() and (RetryCount < 3) do
  begin
    Log('Final application close check (attempt ' + IntToStr(RetryCount + 1) + ')');
    KillTask('timesync.exe');
    Sleep(1000);
    RetryCount := RetryCount + 1;
  end;

  if IsApplicationRunning() then
  begin
    Log('Warning: Application may still be running during installation');
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataDir: String;
  TempDir: String;
  CompletionFile: String;
  UpdatePendingFile: String;
  LogContent: String;
  CurrentVersion: String;
begin
  if CurStep = ssInstall then
  begin
    Log('Installation step started at: ' + InstallationStartTime);
  end;

  if CurStep = ssPostInstall then
  begin
    Log('Post-installation setup beginning');

    // Create required directories
    if not DirExists(ExpandConstant('{app}\logs')) then
    begin
      CreateDir(ExpandConstant('{app}\logs'));
      Log('Created logs directory');
    end;

    if not DirExists(ExpandConstant('{app}\exports')) then
    begin
      CreateDir(ExpandConstant('{app}\exports'));
      Log('Created exports directory');
    end;

    if not DirExists(ExpandConstant('{app}\backup')) then
    begin
      CreateDir(ExpandConstant('{app}\backup'));
      Log('Created backup directory');
    end;

    // Create AppData directory for the application
    AppDataDir := ExpandConstant('{userappdata}\timesync');
    if not DirExists(AppDataDir) then
    begin
      CreateDir(AppDataDir);
      Log('Created AppData directory: ' + AppDataDir);
    end;

    // Create update completion verification file
    TempDir := GetTempDir();
    CompletionFile := TempDir + 'timesync_update_complete';
    UpdatePendingFile := TempDir + 'timesync_update_pending';

    // Get the current version being installed
    CurrentVersion := '{#AppVersion}';

    // Create completion log content
    LogContent := 'Installation completed successfully' + #13#10 +
                  'Version: ' + CurrentVersion + #13#10 +
                  'Install Path: ' + ExpandConstant('{app}') + #13#10 +
                  'Installation Time: ' + InstallationStartTime + #13#10 +
                  'Completion Time: ' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', #0, #0);

    // Write completion file
    if SaveStringToFile(CompletionFile, LogContent, False) then
    begin
      Log('Created update completion file: ' + CompletionFile);
    end
    else
    begin
      Log('Failed to create update completion file');
    end;

    // Clean up pending file if it exists
    if FileExists(UpdatePendingFile) then
    begin
      if DeleteFile(UpdatePendingFile) then
      begin
        Log('Cleaned up update pending file');
      end
      else
      begin
        Log('Failed to clean up update pending file');
      end;
    end;

    Log('Post-installation setup completed');
  end;
end;

function InitializeUninstall(): Boolean;
var
  TaskKillPath: String;
  ResultCode: Integer;
  RetryCount: Integer;
begin
  Log('Uninstallation starting');

  // Kill the application process if it's running
  RetryCount := 0;
  while IsApplicationRunning() and (RetryCount < 5) do
  begin
    Log('Attempting to close application for uninstall (attempt ' + IntToStr(RetryCount + 1) + ')');

    TaskKillPath := ExpandConstant('{sys}\taskkill.exe');
    if FileExists(TaskKillPath) then
    begin
      if Exec(TaskKillPath, '/f /im "{#MyAppExeName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      begin
        Log('Attempted to terminate running application processes');
      end;
    end;

    Sleep(2000);
    RetryCount := RetryCount + 1;
  end;

  if IsApplicationRunning() then
  begin
    Log('Warning: Application may still be running during uninstall');
  end else
  begin
    Log('Application successfully closed for uninstall');
  end;

  Result := True;
end;

procedure DeinitializeSetup();
begin
  // Clean up any temporary files or perform final tasks
  Log('Setup completed - performing cleanup');
end;