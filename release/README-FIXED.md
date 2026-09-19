# CSL-Tools v1.6.0 - ИСПРАВЛЕННЫЕ EXE - РЕШЕНИЕ "EXE НЕ ЗАПУСКАЮТСЯ"

## Проблема
Старые EXE (CSL-Tools-Windows-Single.exe 4.6Мб) не запускались из-за:
- Отсутствия msvcrt DLL (ucrtbase.dll, api-ms-win-*.dll)
- Отсутствия tkinter (_tkinter.pyd, tcl/tk)
- Linux сборки PyInstaller (30Мб) не работает на Windows

## Решение - 3 рабочих варианта

### ✅ Вариант 1 - ГАРАНТИРОВАННЫЙ (работает всегда, без Python)
**Файлы: `CSL-Tools.bat` + `CSL-Tools-PowerShell.ps1`**

- Чистый PowerShell, не требует Python, не требует DLL
- Работает на любой Windows 10/11
- Делает всё: ipconfig, ping, tracert, DNS, VPN/Proxy, BSOD, отчет
- Отправка на admin@csl.by через Outlook/mailto

**Запуск:**
```
Двойной клик по CSL-Tools.bat
Или: PowerShell -ExecutionPolicy Bypass -File CSL-Tools-PowerShell.ps1
Запуск от Администратора для полного функционала
```

### ✅ Вариант 2 - CONSOLE FIXED EXE (5.6 Мб) - ИСПРАВЛЕН
**Файлы: `CSL-Tools-Console-Fixed.exe`**

- Настоящий Windows PE32+ console EXE
- Включает ВСЕ необходимые DLL: python310.dll, vcruntime140.dll, ucrtbase.dll, api-ms-win-*.dll
- Не требует tkinter, консольная версия (показывает логи)
- Собран с Windows bootloader + PKG с Python embed 64-bit
- **Где:** `dist/CSL-Tools-Console-Fixed.exe`, `release/`

Если не запускается:
- Установите VC++ Redist 2015-2022: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Добавьте в исключения антивируса

### ✅ Вариант 3 - GUI FIXED EXE (5.6 Мб)
**Файлы: `CSL-Tools-GUI-Fixed.exe`**

- GUI версия (windowed), fallback в консоль если нет tkinter
- Те же DLL что и console

### 📦 Портативная версия
**`CSL-Tools-Windows-Portable.zip` (14 Мб)**
- Распакуйте → `CSL-Tools.bat`
- Содержит Python embed + main.py + CSL-Tools.exe (98Кб PE32)

### 📦 Финальный bundle (рекомендуется)
**`CSL-Tools-FINAL-WINDOWS.zip` (20 Мб)**
- Включает ВСЕ рабочие варианты:
  - CSL-Tools.bat + CSL-Tools-PowerShell.ps1 (гарантированный)
  - CSL-Tools-Console-Fixed.exe (5.6Мб)
  - CSL-Tools-GUI-Fixed.exe (5.6Мб)
  - CSL-Tools-Windows-Single.exe (4.6Мб старый)
  - README, LICENSE, иконки

## Что делать если EXE не запускаются

1. **Используйте CSL-Tools.bat** - работает всегда
2. Установите Visual C++ Redistributable x64: https://aka.ms/vs/17/release/vc_redist.x64.exe
3. Запустите от имени Администратора (правый клик)
4. Проверьте антивирус - добавьте папку в исключения
5. Попробуйте PowerShell напрямую: `powershell -ExecutionPolicy Bypass -File CSL-Tools-PowerShell.ps1`

## Проверка EXE

```bat
file CSL-Tools-Console-Fixed.exe
# Должно быть: PE32+ executable for MS Windows 6.00 (console), x86-64

file CSL-Tools-Windows-Portable/CSL-Tools.exe
# Должно быть: PE32 executable for MS Windows 6.00 (GUI), Intel i386
```

Linux сборка `CSL-Tools.exe` 30Мб - это ELF, на Windows не работает, нужно пересобрать через `build_exe.bat` на Windows.

## Отправка на admin@csl.by

PowerShell версия автоматически сохраняет отчет на Рабочий стол и предлагает отправить через Outlook/mailto на admin@csl.by

## Поддержка

ООО «Компьютерная безопасность» | csl.by
admin@csl.by | +375 29 337 14 12
Минск, Фабрициуса 9
