; CSL-Tools Installer - Inno Setup Script
; ООО «Компьютерная безопасность» | csl.by | admin@csl.by
; Версия 1.6.0

#define MyAppName "CSL-Tools"
#define MyAppVersion "1.6.0"
#define MyAppPublisher "ООО «Компьютерная безопасность»"
#define MyAppURL "https://csl.by"
#define MyAppExeName "CSL-Tools.exe"

[Setup]
AppId={{8C4E5F2A-9B3D-4E7F-A1C2-D3E4F5A6B7C8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=no
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=CSL-Tools-Setup-v{#MyAppVersion}
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
WizardImageFile=icon.png
WizardSmallImageFile=icon.png
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\CSL-Tools.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion; Permissions: everyone-read
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; WorkingDir: "{app}"; Comment: "CSL-Tools - Сетевая диагностика csl.by"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\icon.ico"; WorkingDir: "{app}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
Filename: "https://csl.by"; Description: "Открыть сайт csl.by"; Flags: postinstall shellexec skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}\temp_reports"
Type: files; Name: "{app}\*.log"

[Code]
var
  EmailPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  EmailPage := CreateInputQueryPage(wpSelectTasks,
    'Контактные данные', 'Для отправки отчетов на admin@csl.by',
    'Укажите вашу организацию и телефон (необязательно, можно заполнить позже в программе).');
  EmailPage.Add('Организация / ФИО:', False);
  EmailPage.Add('Телефон:', False);
end;

function GetEmail(Param: String): String;
begin
  Result := EmailPage.Values[0] + ' | ' + EmailPage.Values[1];
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir, ConfigFile, JsonContent: String;
begin
  if CurStep = ssPostInstall then
  begin
    ConfigDir := ExpandConstant('{userappdata}\CSL-Tools');
    ConfigFile := ConfigDir + '\email_config.json';
    if not DirExists(ConfigDir) then
      CreateDir(ConfigDir);
    
    JsonContent := '{' + #13#10 +
      '  "smtp_server": "mail.csl.by",' + #13#10 +
      '  "smtp_port": 587,' + #13#10 +
      '  "smtp_user": "",' + #13#10 +
      '  "smtp_pass": "",' + #13#10 +
      '  "use_tls": true,' + #13#10 +
      '  "from_email": "",' + #13#10 +
      '  "to_email": "admin@csl.by",' + #13#10 +
      '  "client_name": "' + EmailPage.Values[0] + '",' + #13#10 +
      '  "client_phone": "' + EmailPage.Values[1] + '"' + #13#10 +
      '}';
    SaveStringToFile(ConfigFile, JsonContent, False);
  end;
end;
