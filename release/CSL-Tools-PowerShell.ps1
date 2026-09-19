# CSL-Tools v1.6.0 - PowerShell версия (работает без Python!)
# ООО «Компьютерная безопасность» | csl.by | admin@csl.by
# Запуск: PowerShell -ExecutionPolicy Bypass -File CSL-Tools-PowerShell.ps1
# Или правый клик -> Запуск с помощью PowerShell

param(
    [string]$AdminEmail = "admin@csl.by"
)

$Host.UI.RawUI.WindowTitle = "CSL-Tools v1.6.0 - csl.by - $AdminEmail"
Write-Host "======================================================================" -ForegroundColor Yellow
Write-Host "CSL-Tools v1.6.0 - Сетевая диагностика (PowerShell версия)" -ForegroundColor Cyan
Write-Host "ООО «Компьютерная безопасность» | csl.by | $AdminEmail" -ForegroundColor Green
Write-Host "Минск, Фабрициуса 9 | +375 29 337 14 12 | info@csl.by" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Yellow
Write-Host "Дата: $(Get-Date)" -ForegroundColor White
Write-Host "Компьютер: $env:COMPUTERNAME | Пользователь: $env:USERNAME" -ForegroundColor White
Write-Host "OS: $((Get-CimInstance Win32_OperatingSystem).Caption) $((Get-CimInstance Win32_OperatingSystem).Version)" -ForegroundColor White
Write-Host ""

# Функция логирования
$Report = @()
function Add-Report($text) {
    $global:Report += $text
    Write-Host $text
}

Add-Report "=== CSL-Tools PowerShell Диагностика $(Get-Date) ==="
Add-Report "Компания: ООО «Компьютерная безопасность» | csl.by"
Add-Report ""

# 1. Интернет
Write-Host "[1] Проверка интернета..." -ForegroundColor Yellow
$internetTests = @(
    @{Name="8.8.8.8:53 TCP"; Test={ Test-NetConnection -ComputerName 8.8.8.8 -Port 53 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded }},
    @{Name="1.1.1.1:53 TCP"; Test={ Test-NetConnection -ComputerName 1.1.1.1 -Port 53 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded }},
    @{Name="google.com:443"; Test={ Test-NetConnection -ComputerName google.com -Port 443 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded }},
    @{Name="csl.by:443"; Test={ Test-NetConnection -ComputerName csl.by -Port 443 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded }}
)
$internetOk = $false
foreach ($t in $internetTests) {
    try {
        $res = & $t.Test
        $status = if ($res) { "OK"; $internetOk = $true } else { "FAIL" }
        Add-Report "  $($t.Name): $status"
    } catch {
        Add-Report "  $($t.Name): FAIL - $_"
    }
}
Add-Report "  ИТОГ Интернет: $(if ($internetOk) {'ОК'} else {'НЕТ ДОСТУПА'})"
Add-Report ""

# 2. Адаптеры
Write-Host "[2] Сетевые адаптеры..." -ForegroundColor Yellow
try {
    $adapters = Get-NetAdapter | Where-Object Status -eq "Up" | Format-List Name, InterfaceDescription, Status, LinkSpeed, MediaConnectionState | Out-String
    Add-Report $adapters
    $ipconfig = ipconfig /all
    Add-Report ($ipconfig | Out-String)
} catch {
    Add-Report "  Ошибка получения адаптеров: $_"
}
Add-Report ""

# 3. VPN/Прокси
Write-Host "[3] Проверка VPN/Прокси..." -ForegroundColor Yellow
try {
    $vpnAdapters = Get-NetAdapter | Where-Object { $_.InterfaceDescription -match "TAP|TUN|VPN|WireGuard|OpenVPN" } | Select-Object Name, InterfaceDescription
    if ($vpnAdapters) {
        Add-Report "  [!] Найдены VPN адаптеры:"
        Add-Report ($vpnAdapters | Format-List | Out-String)
    } else {
        Add-Report "  VPN адаптеры не найдены"
    }

    $proxyEnable = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyEnable -ErrorAction SilentlyContinue
    if ($proxyEnable.ProxyEnable -eq 1) {
        $proxyServer = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name ProxyServer -ErrorAction SilentlyContinue
        Add-Report "  [!] Системный прокси ВКЛЮЧЕН: $($proxyServer.ProxyServer)"
    } else {
        Add-Report "  Системный прокси выключен"
    }

    $winhttp = netsh winhttp show proxy
    Add-Report "  WinHTTP: $winhttp"
} catch {
    Add-Report "  Ошибка VPN/Прокси: $_"
}
Add-Report ""

# 4. DNS/DHCP
Write-Host "[4] DNS/DHCP..." -ForegroundColor Yellow
try {
    $dns = Get-DnsClientServerAddress | Format-List | Out-String
    Add-Report $dns
    Add-Report "  nslookup csl.by:"
    $ns = nslookup csl.by 8.8.8.8 2>&1 | Out-String
    Add-Report $ns

    $hosts = @("google.com", "csl.by", "ya.ru")
    foreach ($h in $hosts) {
        try {
            $ip = [System.Net.Dns]::GetHostAddresses($h) | Select-Object -First 1
            Add-Report "  $h -> $ip OK"
        } catch {
            Add-Report "  $h -> FAIL $_"
        }
    }
} catch {
    Add-Report "  Ошибка DNS: $_"
}
Add-Report ""

# 5. Пинг
Write-Host "[5] Пинг..." -ForegroundColor Yellow
$pingHosts = @("8.8.8.8", "1.1.1.1", "google.com", "csl.by")
foreach ($h in $pingHosts) {
    try {
        $ping = Test-Connection -ComputerName $h -Count 2 -ErrorAction SilentlyContinue
        if ($ping) {
            $avg = ($ping | Measure-Object -Property Latency -Average).Average
            Add-Report "  $h : OK avg ${avg}ms"
        } else {
            Add-Report "  $h : FAIL"
        }
    } catch {
        # fallback to ping.exe
        $out = ping -n 2 $h 2>&1 | Out-String
        $ok = $out -match "TTL"
        Add-Report "  $h : $(if ($ok) {'OK'} else {'FAIL'})"
    }
}
Add-Report ""

# 6. Трассировка
Write-Host "[6] Трассировка до 8.8.8.8 и csl.by..." -ForegroundColor Yellow
try {
    $trace1 = tracert -d -h 15 8.8.8.8 2>&1 | Out-String
    Add-Report "  tracert 8.8.8.8:`n$trace1"
    $trace2 = tracert -d -h 15 csl.by 2>&1 | Out-String
    Add-Report "  tracert csl.by:`n$trace2"
} catch {
    Add-Report "  Ошибка трассировки: $_"
}
Add-Report ""

# 7. BSOD
Write-Host "[7] BlueScreen (BSOD)..." -ForegroundColor Yellow
try {
    $minidump = "C:\Windows\Minidump"
    if (Test-Path $minidump) {
        $dumps = Get-ChildItem $minidump -Filter *.dmp | Sort-Object LastWriteTime -Descending | Select-Object -First 5
        Add-Report "  Найдено дампов: $($dumps.Count)"
        foreach ($d in $dumps) {
            Add-Report "    $($d.LastWriteTime) | $($d.Name) | $([math]::Round($d.Length/1KB)) KB"
        }
    } else {
        Add-Report "  Папка Minidump не найдена"
    }

    $memDump = "C:\Windows\MEMORY.DMP"
    if (Test-Path $memDump) {
        $size = (Get-Item $memDump).Length / 1MB
        Add-Report "  MEMORY.DMP найден: $([math]::Round($size)) MB"
    }

    $events = Get-WinEvent -FilterHashtable @{LogName='System'; ID=1001,41} -MaxEvents 5 -ErrorAction SilentlyContinue | Format-List TimeCreated, Id, LevelDisplayName, Message | Out-String
    if ($events) {
        Add-Report "  Журнал BugCheck:`n$events"
    } else {
        Add-Report "  BSOD в журнале не найдено"
    }
} catch {
    Add-Report "  Ошибка BSOD: $_"
}
Add-Report ""

# 8. Исправление (предложения)
Write-Host "[8] Рекомендации..." -ForegroundColor Yellow
if (-not $internetOk) {
    Add-Report "  - Нет интернета: попробуйте ipconfig /release, /renew, netsh winsock reset"
}
Add-Report "  - Для сброса DNS: ipconfig /flushdns"
Add-Report "  - Для сброса сети: netsh winsock reset + netsh int ip reset + перезагрузка"
Add-Report "  - Для отключения прокси: reg add HKCU\...\Internet Settings /v ProxyEnable /d 0 /f + netsh winhttp reset proxy"
Add-Report ""

Add-Report "======================================================================"
Add-Report "Отчет подготовлен CSL-Tools v1.6.0 | csl.by | admin@csl.by"
Add-Report "Для поддержки: +375 29 337 14 12 | info@csl.by"
Add-Report "======================================================================"

# Сохранение отчета
$desktop = [Environment]::GetFolderPath("Desktop")
if (-not $desktop -or -not (Test-Path $desktop)) {
    $desktop = "$env:USERPROFILE\Desktop"
}
if (-not (Test-Path $desktop)) {
    $desktop = $PWD.Path
}
$reportPath = Join-Path $desktop "CSL-Tools_Report_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
try {
    $Report | Out-File -FilePath $reportPath -Encoding utf8
    Write-Host ""
    Write-Host "Отчет сохранен: $reportPath" -ForegroundColor Green
} catch {
    Write-Host "Не удалось сохранить отчет: $_" -ForegroundColor Red
}

# Отправка на admin@csl.by
Write-Host ""
Write-Host "Хотите отправить отчет на $AdminEmail ?" -ForegroundColor Yellow
$send = Read-Host "Отправить? (Y/n) - откроет почтовый клиент с вложением"

if ($send -eq "" -or $send -match "^[YyДд]") {
    try {
        $subject = "[CSL-Tools] Отчет $env:COMPUTERNAME $(Get-Date -Format 'dd.MM.yyyy HH:mm')"
        $body = "Здравствуйте, CSL!`n`nОтчет диагностики во вложении.`n`nКомпьютер: $env:COMPUTERNAME`nДата: $(Get-Date)`n`n---`nCSL-Tools v1.6.0 | csl.by | $AdminEmail"

        # Попытка через Outlook
        try {
            $Outlook = New-Object -ComObject Outlook.Application -ErrorAction Stop
            $Mail = $Outlook.CreateItem(0)
            $Mail.To = $AdminEmail
            $Mail.Subject = $subject
            $Mail.Body = $body
            if (Test-Path $reportPath) {
                $Mail.Attachments.Add($reportPath)
            }
            $Mail.Display()
            Write-Host "Outlook открыт с письмом на $AdminEmail" -ForegroundColor Green
        } catch {
            # Fallback mailto
            $mailto = "mailto:$AdminEmail`?subject=$([uri]::EscapeDataString($subject))&body=$([uri]::EscapeDataString($body))"
            Start-Process $mailto
            Write-Host "Почтовый клиент открыт (mailto). Прикрепите файл вручную: $reportPath" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Ошибка отправки: $_" -ForegroundColor Red
        Write-Host "Отправьте файл вручную на $AdminEmail : $reportPath" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Для исправления сети запустите от Администратора и выполните:" -ForegroundColor Cyan
Write-Host "  ipconfig /flushdns" -ForegroundColor White
Write-Host "  ipconfig /release; ipconfig /renew" -ForegroundColor White
Write-Host "  netsh winsock reset; netsh int ip reset; netsh winhttp reset proxy" -ForegroundColor White
Write-Host "  Restart-NetAdapter -Name (Get-NetAdapter | Where Status -eq Up | Select -First 1).Name -Confirm:`$false" -ForegroundColor White
Write-Host ""
Write-Host "Нажмите Enter для выхода..." -ForegroundColor Yellow
Read-Host
