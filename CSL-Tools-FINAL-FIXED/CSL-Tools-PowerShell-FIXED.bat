@echo off
chcp 65001 >nul
title CSL-Tools PowerShell - гарантированный запуск
color 0E
echo Запуск PowerShell версии CSL-Tools...
echo Этот вариант работает ВСЕГДА, даже если EXE не работают
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0CSL-Tools-PowerShell.ps1"
echo.
echo Нажмите любую клавишу...
pause >nul
