; TimeAttendanceSystem-Installer.iss
#define AppName "Time Attendance System"
#define AppVersion "1.0.0"
#define AppPublisher "Business Platforms"
#define AppURL "https://www.yourcompany.com"
#define AppExeName "TimeAttendanceSystem.exe"
#define AppDataFolder "TimeAttendanceSystem"

[Setup]
AppId={{5DAB2F70-8AC3-45C4-AE39-9F06BE1B4D5F}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={commonpf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=TimeAttendanceSystem-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=admin
SetupIconFile=assets\timesync-logo.ico
UninstallDisplayIcon={app}\{#AppExeName}
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start the application when Windows starts"; GroupDescription: "Windows Startup"

[Files]
; Main executable
Source: "dist\TimeAttendanceSystem.exe"; DestDir: "{app}"; Flags: ignoreversion

; Create necessary folders (no need to include data folder in app directory)
Source: "dist\logs\*"; DestDir: "{app}\logs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\exports\*"; DestDir: "{app}\exports"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\backup\*"; DestDir: "{app}\backup"; Flags: ignoreversion recursesubdirs createallsubdirs

; Create update folder
Source: "updater\*"; DestDir: "{app}\updater"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.db"

[Dirs]
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\exports"; Permissions: users-modify
Name: "{app}\backup"; Permissions: users-modify
; Make sure the AppData directory exists for the database
Name: "{userappdata}\{#AppDataFolder}"; Permissions: users-modify

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{commonstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  BackupFileName: String;
  AppDataDBPath: String;
begin
  // Path to the database in AppData
  AppDataDBPath := ExpandConstant('{userappdata}\{#AppDataFolder}\attendance.db');

  // Check if the database file exists in the AppData directory
  if FileExists(AppDataDBPath) then
  begin
    // Create backup filename with timestamp
    BackupFileName := ExpandConstant('{app}\backup\attendance.db_' + GetDateTimeString('yyyy-mm-dd_hh-nn-ss', '-', '-'));

    // Create backup directory if it doesn't exist
    if not ForceDirectories(ExpandConstant('{app}\backup')) then
      MsgBox('Could not create backup directory!', mbError, MB_OK);

    // Backup the database file
    if not FileCopy(AppDataDBPath, BackupFileName, false) then
      MsgBox('Could not backup database file from ' + AppDataDBPath + '!', mbError, MB_OK);

    // Log the backup
    Log('Database backed up from ' + AppDataDBPath + ' to ' + BackupFileName);
  end;

  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataDBDir: String;
  AppDataDBPath: String;
  BackupDir: String;
  FindRec: TFindRec;
  LatestBackup: String;
  LatestTime: Integer;
  CurrentTime: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Paths
    AppDataDBDir := ExpandConstant('{userappdata}\{#AppDataFolder}');
    AppDataDBPath := AppDataDBDir + '\attendance.db';
    BackupDir := ExpandConstant('{app}\backup');

    // Create AppData directory if it doesn't exist
    if not ForceDirectories(AppDataDBDir) then
      MsgBox('Could not create AppData directory: ' + AppDataDBDir, mbError, MB_OK);

    // Restore database file from most recent backup if needed
    if DirExists(BackupDir) and not FileExists(AppDataDBPath) then
    begin
      // Initialize latest backup tracking
      LatestBackup := '';
      LatestTime := 0;

      // Find the most recent backup file
      if FindFirst(BackupDir + '\attendance.db_*', FindRec) then
      begin
        try
          repeat
            // Simple timestamp comparison (this could be improved)
            if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY = 0 then
            begin
              CurrentTime := FileAge(BackupDir + '\' + FindRec.Name);
              if CurrentTime > LatestTime then
              begin
                LatestTime := CurrentTime;
                LatestBackup := FindRec.Name;
              end;
            end;
          until not FindNext(FindRec);
        finally
          FindClose(FindRec);
        end;
      end;

      // If we found a backup, restore it
      if LatestBackup <> '' then
      begin
        if not FileCopy(BackupDir + '\' + LatestBackup, AppDataDBPath, false) then
          MsgBox('Could not restore database from backup!', mbError, MB_OK)
        else
          Log('Restored database from ' + LatestBackup + ' to ' + AppDataDBPath);
      end;
    end;
  end;
end;