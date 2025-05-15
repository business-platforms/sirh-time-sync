; timesync-Installer.iss
#define AppName "Time Attendance System"
#define AppVersion "1.0.0"
#define AppPublisher "Business Platforms"
#define AppURL "https://www.yourcompany.com"
#define AppExeName "timesync.exe"
#define AppDataFolder "timesync"
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
OutputBaseFilename=timesync-setup{#AppVersion}
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
Source: "dist\timesync.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\timesync-logo.ico"; DestDir: "{app}"; Flags: ignoreversion
[Dirs]
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\exports"; Permissions: users-modify
Name: "{app}\backup"; Permissions: users-modify
; Make sure the AppData directory exists for the database
Name: "{userappdata}\{#AppDataFolder}"; Permissions: users-modify
[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\timesync-logo.ico"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\timesync-logo.ico"; Tasks: desktopicon
Name: "{commonstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\timesync-logo.ico"; Tasks: startupicon
[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
[Code]
function InitializeSetup(): Boolean;
begin
  // Simply return True - we'll handle database operations during installation
  Result := True;
end;
procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataDBDir: String;
  AppDataDBPath: String;
  BackupDir: String;
  BackupFileName: String;
  FindRec: TFindRec;
  LatestBackup: String;
  CurrentTime: String;
begin
  // Handle backup during installation (after directory is selected but before files are copied)
  if CurStep = ssInstall then
  begin
    AppDataDBDir := ExpandConstant('{userappdata}\{#AppDataFolder}');
    AppDataDBPath := AppDataDBDir + '\attendance.db';
    // Check if the database exists in AppData
    if FileExists(AppDataDBPath) then
    begin
      // Get installation directory and create backup folder
      BackupDir := ExpandConstant('{app}\backup');
      // Create backup directory
      if not ForceDirectories(BackupDir) then
      begin
        MsgBox('Could not create backup directory at: ' + BackupDir, mbError, MB_OK);
      end
      else
      begin
        // Generate a timestamp-like string for the backup filename
        CurrentTime := GetDateTimeString('yyyymmdd_hhnnss', '_', '_');
        if CurrentTime = '' then CurrentTime := 'backup'; // Fallback if function fails
        // Create backup filename
        BackupFileName := BackupDir + '\attendance.db_' + CurrentTime;
        // Backup the database file
        if FileCopy(AppDataDBPath, BackupFileName, false) then
        begin
          Log('Database backed up from ' + AppDataDBPath + ' to ' + BackupFileName);
        end
        else
        begin
          MsgBox('Failed to backup database file from: ' + AppDataDBPath, mbError, MB_OK);
        end;
      end;
    end;
  end;
  // Handle restoration during post-installation
  if CurStep = ssPostInstall then
  begin
    // Paths for database
    AppDataDBDir := ExpandConstant('{userappdata}\{#AppDataFolder}');
    AppDataDBPath := AppDataDBDir + '\attendance.db';
    BackupDir := ExpandConstant('{app}\backup');
    // Create AppData directory if it doesn't exist
    if not ForceDirectories(AppDataDBDir) then
      MsgBox('Could not create AppData directory: ' + AppDataDBDir, mbError, MB_OK);
    // Restore database file from backup if needed
    if DirExists(BackupDir) and not FileExists(AppDataDBPath) then
    begin
      // Initialize latest backup tracking
      LatestBackup := '';
      // Find any backup file
      if FindFirst(BackupDir + '\attendance.db_*', FindRec) then
      begin
        try
          // Use the first backup file we find
          if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY = 0 then
          begin
            LatestBackup := FindRec.Name;
          end;
          // Look through all backup files
          while FindNext(FindRec) do
          begin
            if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY = 0 then
            begin
              // Just use the last file we find for simplicity
              LatestBackup := FindRec.Name;
            end;
          end;
        finally
          FindClose(FindRec);
        end;
      end;
      // If we found a backup, restore it
      if LatestBackup <> '' then
      begin
        if FileCopy(BackupDir + '\' + LatestBackup, AppDataDBPath, false) then
          Log('Restored database from ' + LatestBackup + ' to ' + AppDataDBPath)
        else
          MsgBox('Could not restore database from backup!', mbError, MB_OK);
      end;
    end;
  end;
end;