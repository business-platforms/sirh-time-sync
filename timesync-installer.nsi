# Time Attendance System - NSIS Script
# Converted from Inno Setup

!define APP_NAME "Time Attendance System"
!define APP_VERSION "1.0.6"
!define APP_PUBLISHER "Business Platforms"
!define APP_URL "https://business-platforms.com"
!define APP_EXE "timesync"
!define APP_GUID "{A1B2C3D4-E5F6-4A5B-8C7D-9E0F1A2B3C4D}"

# Modern UI
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

# Installer settings
Name "${APP_NAME}"
OutFile "installer\timesync-setup-${APP_VERSION}.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallPath"
RequestExecutionLevel admin
ShowInstDetails show
ShowUnInstDetails show

# Version information
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "FileDescription" "${APP_NAME} Installer"
VIAddVersionKey "LegalCopyright" "© ${APP_PUBLISHER}"

# Modern UI settings
!define MUI_ABORTWARNING
!define MUI_ICON "assets\timesync-logo.ico"
!define MUI_UNICON "assets\timesync-logo.ico"
!define MUI_HEADERIMAGE

# Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

# Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

# Languages
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "English"

# Component descriptions
LangString DESC_MainSection ${LANG_FRENCH} "Application principale"
LangString DESC_MainSection ${LANG_ENGLISH} "Main application"
LangString DESC_DesktopIcon ${LANG_FRENCH} "Créer un raccourci sur le bureau"
LangString DESC_DesktopIcon ${LANG_ENGLISH} "Create desktop shortcut"
LangString DESC_StartupIcon ${LANG_FRENCH} "Lancer au démarrage de Windows"
LangString DESC_StartupIcon ${LANG_ENGLISH} "Launch at Windows startup"

# Sections
Section "!${APP_NAME}" SEC_MAIN
    SectionIn RO  # Required section

    # Close running application
    DetailPrint "Fermeture de l'application..."
    nsExec::ExecToLog 'taskkill /f /im "${APP_EXE}" /t'
    Sleep 2000

    SetOutPath "$INSTDIR"

    # Install main files
    File "dist\${APP_EXE}"
    File /r "dist/*"

    # Create directories
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\exports"
    CreateDirectory "$INSTDIR\backup"

    # Create AppData directory
    CreateDirectory "$APPDATA\timesync"

    # Registry entries
    WriteRegStr HKLM "Software\${APP_NAME}" "InstallPath" "$INSTDIR"
    WriteRegStr HKLM "Software\${APP_NAME}" "Version" "${APP_VERSION}"

    # Uninstaller registry
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "NoRepair" 1

    # Calculate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "EstimatedSize" "$0"

    # Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    # Create program menu folder
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Désinstaller.lnk" "$INSTDIR\uninstall.exe"

    # Create update completion file
    FileOpen $0 "$TEMP\timesync_update_complete" w
    FileWrite $0 "Installation completed successfully$\r$\n"
    FileWrite $0 "Version: ${APP_VERSION}$\r$\n"
    FileWrite $0 "Install Path: $INSTDIR$\r$\n"
    FileClose $0

SectionEnd

Section "Raccourci Bureau" SEC_DESKTOP
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

Section "Lancement automatique" SEC_STARTUP
    CreateShortCut "$SMSTARTUP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

# Component descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_MAIN} $(DESC_MainSection)
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DESKTOP} $(DESC_DesktopIcon)
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_STARTUP} $(DESC_StartupIcon)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

# Uninstaller section
Section "Uninstall"
    # Close running application
    nsExec::ExecToLog 'taskkill /f /im "${APP_EXE}" /t'
    Sleep 2000

    # Remove files
    Delete "$INSTDIR\${APP_EXE}"
    Delete "$INSTDIR\uninstall.exe"
    RMDir /r "$INSTDIR\logs"
    RMDir /r "$INSTDIR\exports"
    RMDir /r "$INSTDIR\backup"
    RMDir /r "$INSTDIR"

    # Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMSTARTUP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"

    # Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}"
    DeleteRegKey HKLM "Software\${APP_NAME}"

    # Note: We don't remove AppData directory to preserve user data
SectionEnd

# Functions
Function .onInit
    # Check for existing installation
    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "UninstallString"
    StrCmp $R0 "" done

    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "Une version de ${APP_NAME} est déjà installée. Voulez-vous la désinstaller d'abord?" \
        /SD IDCANCEL IDOK uninst
    Abort

    uninst:
        ClearErrors
        ExecWait '$R0 /S _?=$INSTDIR'

        IfErrors no_remove_uninstaller done
        no_remove_uninstaller:

    done:
FunctionEnd