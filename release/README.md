# CSL-Tools — Сетевая диагностика

**Версия 1.5.0**  
**ООО «Компьютерная безопасность»** | [csl.by](https://csl.by)  
г. Минск, ул. Фабрициуса 9 | +375 29 337 14 12 | info@csl.by  
Пн-Пт 9:00-17:00

Фирменный стиль: оранжевый #FF7A00, белый, темный #1F1F1F — как на сайте csl.by

---

## Что делает программа

CSL-Tools — это all-in-one утилита для диагностики сети на Windows, разработанная для клиентов CSL.

### 1. Мониторинг сети
- Авто-диагностика в 1 клик
- Карточки статуса: Интернет, Адаптеры, VPN/Прокси, DNS/DHCP, Пинг, BSOD
- Генерация отчета

### 2. Сетевые карты
- `ipconfig /all`, `Get-NetAdapter`, `netsh interface ip show config`
- `psutil` детали: IP, маска, статус UP/DOWN, скорость
- Определение DHCP

### 3. VPN и Прокси
- Поиск адаптеров: TAP, TUN, WireGuard, OpenVPN, Nord, L2TP, PPTP, ZeroTier, Hamachi
- Поиск процессов VPN в tasklist
- Проверка прокси:
  - Реестр `HKCU\...\Internet Settings\ProxyEnable`
  - `ProxyServer`, `AutoConfigURL`
  - `netsh winhttp show proxy`
  - Переменные окружения http_proxy

### 4. Пинг и Трассировка
- Настраиваемый список хостов (по умолчанию: 8.8.8.8, 1.1.1.1, google.com, csl.by)
- Ping (4 пакета)
- Tracert / traceroute до 20 хопов
- Подсчет успешных

### 5. DNS / DHCP / Интернет
- DNS сервера из ipconfig и Get-DnsClientServerAddress
- Проверка резолва: google.com, csl.by, ya.ru, microsoft.com
- nslookup csl.by 8.8.8.8
- Проверка интернета: TCP 8.8.8.8:53, HTTPS google.com, csl.by
- DHCP enabled

### 6. Исправление ошибок
Все с кнопок, требует Админа:
- 🧹 `ipconfig /flushdns` + `netsh winsock reset`
- 🔄 `ipconfig /release` + `/renew`
- ♻ `netsh int ip reset` + `winsock reset` + `advfirewall reset`
- 🚫 Отключить прокси (реестр + winhttp reset)
- 🌐 DNS Авто / Google (8.8.8.8 + 1.1.1.1)
- 🔌 Перезапуск адаптера `Restart-NetAdapter`
- 🔥 Полный сброс

### 7. BlueScreen
- Чтение `C:\Windows\Minidump\*.dmp` (дата, размер)
- Проверка `C:\Windows\MEMORY.DMP`
- Журнал событий: `Get-WinEvent ID 1001,41,1003` (BugCheck)
- `CrashControl` реестр
- На Linux: `dmesg | panic/oops` и `/var/crash`

### 8. Отчет
- Сохранение на Рабочий стол: `CSL-Tools_Report_YYYYMMDD_HHMMSS.txt`
- Включает все проверки + рекомендации

---

## Установка и запуск

### Вариант A: EXE (для Windows)
1. Скачайте `dist/CSL-Tools.exe`
2. Правый клик → Запуск от имени Администратора (для полного функционала)
3. Нажмите «Запустить полную диагностику»

### Вариант B: Из исходников
```bash
pip install psutil requests pillow
python main.py
```

### Собрать EXE самому на Windows
```bat
build_exe.bat
```
Или вручную:
```bat
pip install pyinstaller psutil requests pillow
pyinstaller --onefile --windowed --name CSL-Tools --icon=icon.ico main.py
```
EXE появится в `dist/`

---

## Скриншоты интерфейса
- Оранжевый header как на csl.by
- Левое темное меню навигации
- Светлый контент, карточки статуса
- Логи: темный для дашборда/пинга/фикса, светлый для адаптеров

## Безопасность
- Не отправляет данные наружу
- Только локальные системные команды
- Открытый исходник

## Поддержка
ООО «Компьютерная безопасность»
- Сайт: https://csl.by
- Телефон: +375 29 337 14 12
- Email: info@csl.by
- Адрес: Минск, ул. Фабрициуса 9

Если CSL-Tools не помог — нажмите 🆘 в программе.

---
© 2026 CSL-Tools для csl.by
