@echo off
chcp 65001 >nul
title CSL-Tools v1.6.0 - csl.by - admin@csl.by
color 0E
echo ======================================================================
echo  CSL-Tools v1.6.0 - Сетевая диагностика
echo  ООО "Компьютерная безопасность" ^| csl.by ^| admin@csl.by
echo  Минск, Фабрициуса 9 ^| +375 29 337 14 12
echo ======================================================================
echo.

:: Проверка прав администратора
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo [!] Запущено БЕЗ прав Администратора
  echo     Для полного функционала (сброс сети, BSOD) запустите от Администратора
  echo     Правый клик -^> Запуск от имени Администратора
  echo.
) else (
  echo [OK] Запущено от Администратора
  echo.
)

:: Проверка наличия PowerShell
where powershell >nul 2>&1
if %errorlevel% neq 0 (
  echo [FAIL] PowerShell не найден!
  pause
  exit /b
)

:: Запуск PowerShell версии (гарантированно работает без Python)
echo [1/2] Запуск PowerShell диагностики...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0CSL-Tools-PowerShell.ps1"

:: Если есть Python версия, предложить
if exist "%~dp0CSL-Tools-Windows-Single.exe" (
  echo.
  echo Найден EXE: CSL-Tools-Windows-Single.exe
  echo Хотите запустить GUI версию? (требует Windows)
  set /p choice="Запустить GUI? (y/N): "
  if /i "%choice%"=="y" (
    start "" "%~dp0CSL-Tools-Windows-Single.exe"
  )
)

if exist "%~dp0CSL-Tools.exe" (
  echo.
  echo Найден Python EXE: CSL-Tools.exe
  echo.
)

echo.
echo ======================================================================
echo  Готово! Отчет на Рабочем столе
echo  Для поддержки: admin@csl.by / +375 29 337 14 12 / csl.by
echo ======================================================================
pause
