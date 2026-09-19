# CSL-Tools v1.6.0 — Сетевая диагностика + Отправка на admin@csl.by + Инсталлятор

**ООО «Компьютерная безопасность»** | [csl.by](https://csl.by)  
г. Минск, ул. Фабрициуса 9 | +375 29 337 14 12 | **admin@csl.by** / info@csl.by  
Пн-Пт 9:00-17:00 | 10 лет • 160 серверов • 80 клиентов

Фирменный стиль: оранжевый #FF7A00 как на csl.by

---

## Что нового в 1.6.0

1. **Отправка отчета на admin@csl.by прямо из программы**
   - Вкладка `Отчет + Email` → поля Организация/Телефон/ПК
   - Кнопка `📧 Отправить на admin@csl.by (SMTP)` — отправка через SMTP с вложением
   - Кнопка `📨 Открыть в Outlook / Почте` — открывает Outlook с письмом и вложением, fallback на mailto
   - Настройки SMTP: `⚙ SMTP` → сервер, порт, логин, пароль, TLS
   - Конфиг хранится в `%APPDATA%\CSL-Tools\email_config.json`
   - Автосохранение отчета в `temp_reports/` и на Рабочий стол

2. **Инсталляторы**
   - **Inno Setup**: `CSL-Tools.iss` → `CSL-Tools-Setup-v1.6.0.exe` (профессиональный установщик, ярлыки, деинсталляция)
   - **Python self-extracting**: `CSL-Tools-Installer.exe` — копирует в Program Files, ярлыки Desktop/Start Menu
   - **PowerShell**: `Install-CSLTools.ps1` — установка одной командой от Админа
   - `build_installer.bat` — собирает все варианты

---

## Функционал диагностики

- **Дашборд**: авто-диагностика 6 шагов + отправка
- **Сетевые карты**: ipconfig /all, Get-NetAdapter, netsh, psutil
- **VPN/Прокси**: TAP/TUN/WireGuard/OpenVPN/Nord, ProxyEnable, WinHTTP
- **Пинг/Трассировка**: настраиваемый список, tracert -d -h 20
- **DNS/DHCP/Интернет**: DNS сервера, nslookup csl.by, резолв 4 доменов, TCP 53, HTTPS
- **Исправление**: flushdns, release/renew, winsock reset, int ip reset, proxy reset, рестарт адаптера, полный сброс
- **BlueScreen**: Minidump, MEMORY.DMP, BugCheck 1001/41
- **Отчет**: сохранение + email

---

## Установка

### Вариант 1 — Inno Setup (рекомендуется)
1. Установите Inno Setup https://jrsoftware.org/isdl.php
2. На Windows запустите `build_installer.bat`
3. Получите `installer_output/CSL-Tools-Setup-v1.6.0.exe`
4. Запустите от Администратора

### Вариант 2 — Python Installer
```
CSL-Tools-Installer.exe (запуск от Администратора)
→ C:\Program Files\CSL-Tools\CSL-Tools.exe
→ Ярлыки Desktop и Start Menu
```

### Вариант 3 — PowerShell
```powershell
Set-ExecutionPolicy Bypass -Scope Process
.\Install-CSLTools.ps1
# или
PowerShell -ExecutionPolicy Bypass -File Install-CSLTools.ps1
```

### Вариант 4 — Портативно
Скопируйте `CSL-Tools.exe` и запускайте от Администратора.

---

## Отправка отчетов на admin@csl.by

### Способ A — SMTP (автоматически)
1. Откройте CSL-Tools → вкладка `Отчет + Email`
2. Заполните Организация / Телефон
3. Нажмите `⚙ SMTP` → укажите:
   - Сервер: `mail.csl.by` или `smtp.yandex.ru` / `smtp.gmail.com` / `smtp.office365.com`
   - Порт: 587 (TLS) или 465 (SSL)
   - Логин: ваш email
   - Пароль: пароль приложения
   - From: ваш email
4. Сохранить → Тест отправки
5. Нажмите `📧 Отправить на admin@csl.by (SMTP)`

Пример конфига `%APPDATA%\CSL-Tools\email_config.json`:
```json
{
  "smtp_server": "mail.csl.by",
  "smtp_port": 587,
  "smtp_user": "support@csl.by",
  "smtp_pass": "****",
  "use_tls": true,
  "from_email": "support@csl.by",
  "to_email": "admin@csl.by",
  "client_name": "ООО Ромашка",
  "client_phone": "+375 29 123-45-67"
}
```

### Способ B — Outlook / Почтовый клиент (без SMTP)
Нажмите `📨 Открыть в Outlook / Почте`:
- Попытается открыть Outlook COM с вложением
- Если Outlook нет — откроет mailto:admin@csl.by
- Файл отчета сохранится в `temp_reports/` — прикрепите вручную если mailto

---

## Сборка EXE на Windows

```bat
build_exe.bat
# dist\CSL-Tools.exe

build_installer.bat
# dist\CSL-Tools.exe
# dist\CSL-Tools-Installer.exe
# installer_output\CSL-Tools-Setup-v1.6.0.exe (если есть Inno Setup)
```

---

## Файлы релиза

- `CSL-Tools.exe` — основная программа v1.6.0
- `CSL-Tools-Installer.exe` — инсталлятор Python
- `CSL-Tools-Setup-v1.6.0.exe` — инсталлятор Inno Setup (собирается на Windows)
- `Install-CSLTools.ps1` — PowerShell инсталлятор
- `CSL-Tools.iss` — скрипт Inno Setup
- `main.py` — исходник
- `installer.py` — исходник инсталлятора
- `icon.ico / icon.png` — иконки
- `LICENSE.txt`, `README.md`, `INSTALL.txt`

---

## Поддержка

ООО «Компьютерная безопасность»
- Сайт: https://csl.by
- Email: **admin@csl.by** / info@csl.by
- Тел: +375 29 337 14 12
- Адрес: Минск, ул. Фабрициуса 9

© 2026 CSL-Tools для csl.by
