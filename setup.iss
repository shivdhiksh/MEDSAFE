; Inno Setup Script for MEDSAFE
; Offline Medicine Expiry Tracker
; Per-User Windows Installation (No Admin Rights Required)

#define MyAppName "MEDSAFE"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Shiva Dhikshith"
#define MyAppURL "https://github.com/shivad18/MEDSAFE"
#define MyAppExeName "MedSafe.exe"

[Setup]
; Unique AppId for upgrade detection across versions
AppId={{8B8497C0-D261-4B78-9B6C-7742A9DF27D0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\MedSafe
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Per-user installation model: no administrator elevation required
PrivilegesRequired=lowest
OutputDir=dist\installer
OutputBaseFilename=MedSafe_Setup_v1.0
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UsePreviousAppDir=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "scheduledtask"; Description: "Enable daily 9:00 AM expiry check notifications in background"; GroupDescription: "Notifications:"; Flags: unchecked

[Files]
Source: "dist\MedSafe\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Do NOT include data/medsafe.db or backups/ here to ensure clean user state.

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Optional Windows Scheduled Task creation
Filename: "schtasks.exe"; Parameters: "/Create /TN ""MEDSAFE Daily Expiry Check"" /TR ""\""{app}\{#MyAppExeName}\"" --check-notifications"" /SC DAILY /ST 09:00 /F"; Flags: runhidden; Tasks: scheduledtask; StatusMsg: "Configuring daily expiry check notification schedule..."
; Launch application option on finish
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove scheduled task cleanly if it exists
Filename: "schtasks.exe"; Parameters: "/Delete /TN ""MEDSAFE Daily Expiry Check"" /F"; Flags: runhidden; RunOnceId: "DeleteMedSafeScheduledTask"

[UninstallDelete]
; Clean up installed application binaries and internal assets in the installation folder
Type: filesandordirs; Name: "{app}"
; NOTE: User data in {localappdata}\MedSafe (database & backups) is strictly preserved and never deleted by the uninstaller.
