@echo off
chcp 65001 >nul
title CSL-Tools FIXED - не закрывается
color 0A
echo ======================================================================
echo  CSL-Tools v1.6.1 FIXED - окно не схлопывается
echo  ООО "Компьютерная безопасность" | csl.by | admin@csl.by
echo ======================================================================
echo.
echo [INFO] Запускаю FIXED Console версию...
echo.

:: Запуск с паузой и логированием
"%~dp0CSL-Tools-FIXED-Console.exe"
set EXITCODE=%errorlevel%

echo.
echo ======================================================================
echo  Код завершения: %EXITCODE%
echo  Если окно пустое - смотрите лог: %TEMP%\CSL-Tools-error.log
echo ======================================================================
echo.
echo  Попытка запуска PowerShell версии (гарантированно работает):
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0CSL-Tools-PowerShell.ps1"

echo.
echo ======================================================================
echo  Готово! Нажмите любую клавишу для выхода...
echo ======================================================================
pause >nul
