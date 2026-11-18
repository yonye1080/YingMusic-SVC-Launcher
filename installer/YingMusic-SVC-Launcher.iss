; ============================================================
;  YingMusic-SVC-Launcher 1.0.0  --  Inno Setup 6 script
;
;  Build:
;    iscc /DPayloadDir="D:\YingMusic-SVC-Portable" ^
;         /DOutDir="D:\YingMusic-SVC-Installer\out" ^
;         YingMusic-SVC-Launcher.iss
;
;  Or simply: build_installer.bat
;
;  Design note: installed per-user (PrivilegesRequired=lowest) into
;  %LocalAppData%\Programs, NOT Program Files. The app writes
;  outputs\, timbre_library\ and ui_lang.json next to its own code,
;  which would fail under Program Files for a non-elevated user.
; ============================================================

#define MyAppName "YingMusic-SVC-Launcher"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "YingMusic-SVC contributors"
#define MyAppURL "https://github.com/yonye1080/YingMusic-SVC-Launcher"

#ifndef PayloadDir
  #define PayloadDir "D:\YingMusic-SVC-Portable"
#endif
#ifndef OutDir
  #define OutDir "D:\YingMusic-SVC-Installer\out"
#endif

[Setup]
AppId={{8F3C2B14-7E52-4A9D-9C1E-2D6A5B8E4F01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
VersionInfoVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutDir}
OutputBaseFilename={#MyAppName}-{#MyAppVersion}-Setup
Compression=lzma2/fast
SolidCompression=no
; The payload is ~9.4 GB, far beyond the 2 GB single-exe limit,
; so disk spanning is mandatory. Result: setup.exe + setup-N.bin slices.
DiskSpanning=yes
DiskSliceSize=2000000000
WizardStyle=modern
UninstallDisplayName={#MyAppName} {#MyAppVersion}
UninstallDisplayIcon={app}\start.bat
AllowNoIcons=yes
; Roughly 9.4 GB unpacked + room for generated audio
ExtraDiskSpaceRequired=0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Everything from the portable bundle. __pycache__/*.pyc are excluded:
; they are regenerated on first run and would add ~20k files / 245 MB.
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__,*.pyc,*.log"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\start.bat"; WorkingDir: "{app}"; Comment: "{#MyAppName} {#MyAppVersion}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\start.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\start.bat"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec

[UninstallDelete]
Type: files; Name: "{app}\ui_lang.json"

[Code]
{ Ask before removing user-generated data on uninstall. }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  OutDir, TimbreDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    OutDir := ExpandConstant('{app}\outputs');
    TimbreDir := ExpandConstant('{app}\timbre_library');
    if DirExists(OutDir) or DirExists(TimbreDir) then
    begin
      if MsgBox('是否同时删除生成的音频与音色库？' + #13#10 +
                'Delete generated audio and the voice library as well?',
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(OutDir, True, True, True);
        DelTree(TimbreDir, True, True, True);
      end;
    end;
  end;
end;
