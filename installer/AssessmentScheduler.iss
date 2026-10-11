#define AppVersion GetEnv('APP_VERSION')
#if AppVersion == ""
  #error "APP_VERSION is required. Set it from main.py or the GitHub release tag."
#endif
[Setup]
AppId={{E4EAD203-3915-4F11-BC6A-7E46C4424DF8}
AppName=Assessment Scheduler
AppVersion={#AppVersion}
DefaultDirName={autopf}\Assessment Scheduler
DefaultGroupName=Assessment Scheduler
OutputDir=..\dist-installer
OutputBaseFilename=AssessmentScheduler_Setup_v{#AppVersion}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\AssessmentScheduler.exe
[Files]
Source: "..\dist\AssessmentScheduler\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\Assessment Scheduler"; Filename: "{app}\AssessmentScheduler.exe"
Name: "{autodesktop}\Assessment Scheduler"; Filename: "{app}\AssessmentScheduler.exe"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce
[Run]
Filename: "{app}\AssessmentScheduler.exe"; Description: "Launch Assessment Scheduler"; Flags: nowait postinstall skipifsilent
