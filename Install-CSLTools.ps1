# CSL-Tools PowerShell Installer
# ООО «Компьютерная безопасность» | csl.by | admin@csl.by
# Запуск: PowerShell -ExecutionPolicy Bypass -File Install-CSLTools.ps1
# Или от Администратора: irm https://csl.by/install.ps1 | iex

param(
    [string]$InstallDir = "$env:ProgramFiles\CSL-Tools",
    [string]$AdminEmail = "admin@csl.by"
)

Write-Host "=== CSL-Tools v1.6.0 Installer ===" -ForegroundColor Yellow
Write-Host "ООО «Компьютерная безопасность» | csl.by | $AdminEmail" -ForegroundColor Cyan

# Проверка админа
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[!] Требуются права Администратора. Перезапуск..." -ForegroundColor Red
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

# Создание папки
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Write-Host "[OK] Папка: $InstallDir" -ForegroundColor Green

# Копирование файлов (если рядом есть dist)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$files = @(
    "$scriptDir\dist\CSL-Tools.exe",
    "$scriptDir\CSL-Tools.exe",
    "$scriptDir\icon.ico",
    "$scriptDir\icon.png",
    "$scriptDir\README.md"
)

$copied = $false
foreach ($f in $files) {
    if (Test-Path $f) {
        Copy-Item $f -Destination $InstallDir -Force
        Write-Host "[OK] Скопирован $f" -ForegroundColor Green
        $copied = $true
    }
}

if (-not $copied) {
    Write-Host "[!] EXE не найден рядом. Скачайте с csl.by или соберите build_exe.bat" -ForegroundColor Yellow
}

# Config для email
$configDir = "$env:APPDATA\CSL-Tools"
New-Item -ItemType Directory -Force -Path $configDir | Out-Null

$clientName = Read-Host "Организация / ФИО (Enter для пропуска)"
$clientPhone = Read-Host "Телефон (Enter для пропуска)"

$config = @{
    smtp_server = "mail.csl.by"
    smtp_port = 587
    smtp_user = ""
    smtp_pass = ""
    use_tls = $true
    from_email = ""
    to_email = $AdminEmail
    client_name = $clientName
    client_phone = $clientPhone
} | ConvertTo-Json -Depth 3

$config | Out-File -FilePath "$configDir\email_config.json" -Encoding utf8
Write-Host "[OK] Config: $configDir\email_config.json" -ForegroundColor Green

# Ярлыки
$WshShell = New-Object -comObject WScript.Shell

# Desktop
$desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$desktop\CSL-Tools.lnk")
$Shortcut.TargetPath = "$InstallDir\CSL-Tools.exe"
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.IconLocation = "$InstallDir\icon.ico"
$Shortcut.Description = "CSL-Tools - Сетевая диагностика csl.by"
$Shortcut.Save()
Write-Host "[OK] Ярлык рабочий стол: $desktop\CSL-Tools.lnk" -ForegroundColor Green

# Start Menu
$startMenu = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\CSL-Tools"
New-Item -ItemType Directory -Force -Path $startMenu | Out-Null
$Shortcut2 = $WshShell.CreateShortcut("$startMenu\CSL-Tools.lnk")
$Shortcut2.TargetPath = "$InstallDir\CSL-Tools.exe"
$Shortcut2.WorkingDirectory = $InstallDir
$Shortcut2.IconLocation = "$InstallDir\icon.ico"
$Shortcut2.Save()
Write-Host "[OK] Ярлык Пуск: $startMenu" -ForegroundColor Green

# Uninstall registry
$regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\CSL-Tools"
New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty -Path $regPath -Name "DisplayName" -Value "CSL-Tools"
Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value "1.6.0"
Set-ItemProperty -Path $regPath -Name "Publisher" -Value "ООО «Компьютерная безопасность»"
Set-ItemProperty -Path $regPath -Name "URLInfoAbout" -Value "https://csl.by"
Set-ItemProperty -Path $regPath -Name "DisplayIcon" -Value "$InstallDir\CSL-Tools.exe"
Set-ItemProperty -Path $regPath -Name "UninstallString" -Value "powershell -File $InstallDir\Uninstall.ps1"

# Uninstall script
@"
Remove-Item -Path "$InstallDir" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$desktop\CSL-Tools.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$startMenu" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\CSL-Tools" -Force -ErrorAction SilentlyContinue
Write-Host "CSL-Tools удален" -ForegroundColor Green
"@ | Out-File -FilePath "$InstallDir\Uninstall.ps1" -Encoding utf8

Write-Host ""
Write-Host "=== Установка завершена! ===" -ForegroundColor Yellow
Write-Host "Папка: $InstallDir"
Write-Host "Отправка: $AdminEmail"
Write-Host "Сайт: https://csl.by | Тел: +375 29 337 14 12"

$run = Read-Host "Запустить CSL-Tools сейчас? (Y/n)"
if ($run -eq "" -or $run -like "Y*") {
    Start-Process "$InstallDir\CSL-Tools.exe"
}
