@echo off
chcp 65001
echo === CSL-Tools v1.6.0 Build EXE ===
echo Компания: ООО "Компьютерная безопасность" csl.by admin@csl.by
echo.

echo Проверка Python...
python --version
if errorlevel 1 (
  echo Python не найден! Установите Python 3.10+
  pause
  exit /b
)

echo Установка зависимостей...
pip install --upgrade pip
pip install psutil requests pillow pyinstaller

echo Очистка старых сборок...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q CSL-Tools.spec 2>nul

echo Сборка EXE с отправкой на admin@csl.by...
pyinstaller --onefile --windowed --name CSL-Tools --icon=icon.ico --add-data "icon.ico;." --add-data "icon.png;." main.py

echo.
if exist dist\CSL-Tools.exe (
  echo [OK] Сборка успешна: dist\CSL-Tools.exe
  dir dist\CSL-Tools.exe
  echo.
  echo Для сборки инсталлятора запустите build_installer.bat
) else (
  echo [FAIL] Сборка не удалась
)

pause
