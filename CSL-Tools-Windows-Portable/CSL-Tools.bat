@echo off
chcp 65001 >nul
echo Запуск CSL-Tools v1.6.0...
echo ООО "Компьютерная безопасность" csl.by admin@csl.by
"%~dp0Python\pythonw.exe" "%~dp0CSL-Tools.launch.pyw" %*
if errorlevel 1 (
  echo Ошибка запуска, пробую консольный режим...
  "%~dp0Python\python.exe" "%~dp0CSL-Tools.launch.pyw" %*
  pause
)
