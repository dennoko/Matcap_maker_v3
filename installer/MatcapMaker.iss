; Inno Setup script for Matcap Maker
; Build via build_installer.py (passes /DAppVersion=<version>).
; Standalone compile (uses the fallback version below): ISCC installer\MatcapMaker.iss

#ifndef AppVersion
  #define AppVersion "3.0.0"
#endif

#define AppName "Matcap Maker"
#define AppPublisher "dennokoworks"
#define AppExeName "MatcapMaker.exe"

[Setup]
AppId={{8F2C7A4E-1B3D-4E5F-9A6B-7C0D1E2F3A4B}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\MatcapMaker
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; --- Icons (must be preserved) ---
SetupIconFile=..\res\icon\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
OutputDir=..\dist\installer
OutputBaseFilename=MatcapMaker-Setup-{#AppVersion}

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; onedir output from PyInstaller (build_exe.py): dist\MatcapMaker\*
Source: "..\dist\MatcapMaker\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
