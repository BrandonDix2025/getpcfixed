[Setup]
AppName=GetPCFixed
AppVersion=0.5
AppVerName=GetPCFixed v0.5
AppPublisher=GetPCFixed
AppPublisherURL=https://getpcfixed.com
DefaultDirName={autopf}\GetPCFixed
DefaultGroupName=GetPCFixed
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=GetPCFixed_Setup_v0.5
WizardStyle=modern
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=admin
UninstallDisplayName=GetPCFixed - AI PC Repair
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\GetPCFixed.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\GetPCFixed.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\GetPCFixed"; Filename: "{app}\GetPCFixed.exe"
Name: "{group}\Uninstall GetPCFixed"; Filename: "{uninstallexe}"
Name: "{commondesktop}\GetPCFixed"; Filename: "{app}\GetPCFixed.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GetPCFixed.exe"; Description: "Launch GetPCFixed now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"