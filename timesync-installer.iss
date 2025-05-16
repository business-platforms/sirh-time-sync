; Time Attendance System - Inno Setup Script
; This script handles installation, updates, and ensures single installation

#define MyAppName "Time Attendance System"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://yourcompany.com"
#define MyAppExeName "timesync.exe"
#define AppVersion "1.0.0"

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
ArchitecturesInstallIn64BitMode=x64

; Always create new log file
SetupLogging=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startupicon"; Description: "Lancer au démarrage de Windows"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\timesync.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
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
function InitializeSetup(): Boolean;
var
  UninstallString: String;
  ResultCode: Integer;
begin
  Result := True;

  // Try to get the uninstaller path of the existing installation
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1',
                         'UninstallString', UninstallString) or
     RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1',
                         'UninstallString', UninstallString) then
  begin
    // Previous installation exists - uninstall it silently without prompting
    if UninstallString <> '' then
    begin
      // Add /SILENT to the uninstaller command
      UninstallString := RemoveQuotes(UninstallString);
      Exec(UninstallString, '/SILENT /NORESTART', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

      // Wait a moment to ensure uninstall completes
      Sleep(2000);
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataDir: String;
  BackupDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Create required directories
    if not DirExists(ExpandConstant('{app}\logs')) then
      CreateDir(ExpandConstant('{app}\logs'));

    if not DirExists(ExpandConstant('{app}\exports')) then
      CreateDir(ExpandConstant('{app}\exports'));

    // Create AppData directory for the application
    AppDataDir := ExpandConstant('{userappdata}\timesync');
    if not DirExists(AppDataDir) then
      CreateDir(AppDataDir);
  end;
end;

function InitializeUninstall(): Boolean;
var
  TaskbarUnpinPath: String;
begin
  // Kill the application process if it's running
  TaskbarUnpinPath := ExpandConstant('{sys}\taskkill.exe');
  Exec(TaskbarUnpinPath, '/f /im "{#MyAppExeName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

  // Allow a moment for the process to close
  Sleep(1000);

  Result := True;
end;