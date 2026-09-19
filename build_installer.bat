@echo off
chcp 65001
echo === CSL-Tools v1.6.0 - Сборка EXE + Инсталлятор ===
echo ООО «Компьютерная безопасность» | csl.by | admin@csl.by
echo.

echo [1/4] Проверка Python...
python --version
if errorlevel 1 (
  echo Python не найден!
  pause
  exit /b
)

echo [2/4] Установка зависимостей...
pip install --upgrade pip
pip install psutil requests pillow pyinstaller

echo [3/4] Сборка CSL-Tools.exe...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q CSL-Tools.spec 2>nul

pyinstaller --onefile --windowed --name CSL-Tools --icon=icon.ico --add-data "icon.ico;." --add-data "icon.png;." main.py

if not exist dist\CSL-Tools.exe (
  echo [FAIL] EXE не собрался
  pause
  exit /b
)
echo [OK] EXE собран: dist\CSL-Tools.exe
dir dist\CSL-Tools.exe

echo [4/4] Сборка инсталлятора...
echo.

REM Попытка собрать через Inno Setup если установлен
where iscc >nul 2>nul
if %errorlevel%==0 (
  echo Inno Setup найден, собираю Setup...
  if not exist installer_output mkdir installer_output
  iscc CSL-Tools.iss
  if exist installer_output\CSL-Tools-Setup-v1.6.0.exe (
    echo [OK] Инсталлятор Inno Setup: installer_output\CSL-Tools-Setup-v1.6.0.exe
  )
) else (
  echo Inno Setup не найден, пропускаю ISS сборку
  echo Скачайте Inno Setup с https://jrsoftware.org/isdl.php для сборки Setup
)

REM Сборка Python инсталлятора (self-extracting)
echo Сборка Python инсталлятора...
pyinstaller --onefile --console --name CSL-Tools-Installer --icon=icon.ico installer.py
if exist dist\CSL-Tools-Installer.exe (
  echo [OK] Python инсталлятор: dist\CSL-Tools-Installer.exe
)

REM Копирование в release
if not exist release mkdir release
copy /y dist\CSL-Tools.exe release\ 2>nul
copy /y dist\CSL-Tools-Installer.exe release\ 2>nul
copy /y main.py release\ 2>nul
copy /y installer.py release\ 2>nul
copy /y Install-CSLTools.ps1 release\ 2>nul
copy /y CSL-Tools.iss release\ 2>nul
copy /y icon.ico release\ 2>nul
copy /y icon.png release\ 2>nul
copy /y README.md release\ 2>nul
copy /y LICENSE.txt release\ 2>nul
if exist installer_output\CSL-Tools-Setup-v1.6.0.exe copy /y installer_output\CSL-Tools-Setup-v1.6.0.exe release\ 2>nul

echo.
echo === ГОТОВО ===
echo Файлы в dist\:
dir dist\*.exe
echo.
echo Файлы в installer_output\:
dir installer_output\*.exe 2>nul
echo.
echo Файлы в release\:
dir release\
echo.
echo Инсталляторы:
echo - CSL-Tools-Setup-v1.6.0.exe (Inno Setup, требует ISCC)
echo - CSL-Tools-Installer.exe (Python self-extracting, работает везде)
echo - Install-CSLTools.ps1 (PowerShell)
echo.
pause
