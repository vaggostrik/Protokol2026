; Inno Setup script for Protokol2026 Windows installer
[Setup]
AppName=Σύστημα Πρωτοκόλλου
AppVersion=1.0.0
AppPublisher=Protokol2026
AppPublisherURL=https://github.com/vaggostrik/Protokol2026
DefaultDirName={autopf}\Protokol2026
DefaultGroupName=Πρωτόκολλο
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=Protokol2026_Setup
SetupIconFile=resources\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
LicenseFile=LICENSE

[Languages]
Name: "greek"; MessagesFile: "compiler:Languages\Greek.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "build\exe.win-amd64-3.*\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Πρωτόκολλο"; Filename: "{app}\Protokol.exe"
Name: "{group}\{cm:UninstallProgram,Πρωτόκολλο}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Πρωτόκολλο"; Filename: "{app}\Protokol.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Protokol.exe"; Description: "{cm:LaunchProgram,Πρωτόκολλο}"; Flags: nowait postinstall skipifsilent
