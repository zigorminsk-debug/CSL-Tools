#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSL-Tools Installer - Python инсталлятор
Устанавливает CSL-Tools в Program Files и создает ярлыки
ООО «Компьютерная безопасность» | csl.by | admin@csl.by
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
import json

APP_NAME = "CSL-Tools"
APP_VERSION = "1.6.0"
ADMIN_EMAIL = "admin@csl.by"

def is_admin():
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        return os.geteuid() == 0

def get_install_dir():
    if platform.system() == "Windows":
        return Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / APP_NAME
    else:
        return Path.home() / APP_NAME

def install():
    print(f"=== {APP_NAME} v{APP_VERSION} Installer ===")
    print(f"ООО «Компьютерная безопасность» | csl.by | {ADMIN_EMAIL}")
    print()

    if platform.system() == "Windows" and not is_admin():
        print("[!] Требуются права Администратора. Перезапуск...")
        try:
            import ctypes
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join([f'"{a}"' for a in sys.argv]), None, 1)
            sys.exit(0)
        except Exception as e:
            print(f"Не удалось повысить права: {e}")
            input("Нажмите Enter для выхода...")
            sys.exit(1)

    install_dir = get_install_dir()
    print(f"Установка в: {install_dir}")
    install_dir.mkdir(parents=True, exist_ok=True)

    # Копируем файлы
    src_dir = Path(__file__).parent
    files_to_copy = ["CSL-Tools.exe", "CSL-Tools", "main.py", "icon.ico", "icon.png", "README.md", "LICENSE.txt"]
    # Попробуем dist/
    dist_dir = src_dir / "dist"
    if dist_dir.exists():
        for f in dist_dir.glob("CSL-Tools*"):
            files_to_copy.append(str(f))

    copied = 0
    for pattern in ["dist/CSL-Tools.exe", "dist/CSL-Tools", "CSL-Tools.exe", "main.py", "icon.ico", "icon.png", "README.md", "LICENSE.txt"]:
        p = src_dir / pattern
        if p.exists() and p.is_file():
            dest = install_dir / p.name
            try:
                shutil.copy2(p, dest)
                print(f"[OK] {p.name} -> {dest}")
                copied += 1
            except Exception as e:
                print(f"[FAIL] {p.name}: {e}")

    if copied == 0:
        # Если запускаем из собранного инсталлятора, сам exe уже внутри
        current_exe = Path(sys.executable) if getattr(sys, 'frozen', False) else None
        if current_exe and current_exe.exists():
            try:
                shutil.copy2(current_exe, install_dir / "CSL-Tools.exe")
                print(f"[OK] Self copy -> {install_dir}")
                copied = 1
            except:
                pass

    # Создаем config
    if platform.system() == "Windows":
        config_dir = Path(os.environ.get("APPDATA", str(Path.home()))) / "CSL-Tools"
    else:
        config_dir = Path.home() / ".config" / "CSL-Tools"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nВведите данные для отправки отчетов (можно пропустить Enter):")
    try:
        client_name = input("Организация / ФИО: ").strip()
        client_phone = input("Телефон: ").strip()
    except:
        client_name = ""
        client_phone = ""

    config = {
        "smtp_server": "mail.csl.by",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_pass": "",
        "use_tls": True,
        "from_email": "",
        "to_email": ADMIN_EMAIL,
        "client_name": client_name,
        "client_phone": client_phone
    }
    with open(config_dir / "email_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"[OK] Config сохранен: {config_dir / 'email_config.json'}")

    # Создаем ярлыки Windows
    if platform.system() == "Windows":
        try:
            # Desktop shortcut via PowerShell
            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                desktop = Path.home() / "Рабочий стол"
            if desktop.exists():
                ps_cmd = f"""
                $WshShell = New-Object -comObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut("{desktop / 'CSL-Tools.lnk'}")
                $Shortcut.TargetPath = "{install_dir / 'CSL-Tools.exe'}"
                $Shortcut.WorkingDirectory = "{install_dir}"
                $Shortcut.IconLocation = "{install_dir / 'icon.ico'}"
                $Shortcut.Description = "CSL-Tools - Сетевая диагностика csl.by"
                $Shortcut.Save()
                """
                subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=10)
                print(f"[OK] Ярлык на рабочем столе: {desktop / 'CSL-Tools.lnk'}")

            # Start Menu
            start_menu = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME
            start_menu.mkdir(parents=True, exist_ok=True)
            ps_cmd2 = f"""
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{start_menu / 'CSL-Tools.lnk'}")
            $Shortcut.TargetPath = "{install_dir / 'CSL-Tools.exe'}"
            $Shortcut.WorkingDirectory = "{install_dir}"
            $Shortcut.IconLocation = "{install_dir / 'icon.ico'}"
            $Shortcut.Save()
            """
            subprocess.run(["powershell", "-Command", ps_cmd2], capture_output=True, timeout=10)
            print(f"[OK] Ярлык в меню Пуск: {start_menu}")

            # Uninstall entry
            try:
                import winreg
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}")
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "ООО «Компьютерная безопасность»")
                winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, "https://csl.by")
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(install_dir / "CSL-Tools.exe"))
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{install_dir / "uninstall.exe"}"')
                winreg.CloseKey(key)
                # Копируем uninstaller (сам инсталлятор)
                if Path(__file__).exists():
                    shutil.copy2(__file__, install_dir / "uninstall.py")
                print("[OK] Запись в Установка/Удаление программ")
            except Exception as e:
                print(f"[WARN] Не удалось создать uninstall запись: {e}")

        except Exception as e:
            print(f"[WARN] Ярлыки: {e}")

    print()
    print(f"=== Установка завершена! ===")
    print(f"Программа установлена в: {install_dir}")
    print(f"Отправка отчетов: {ADMIN_EMAIL}")
    print(f"Сайт: https://csl.by | Тел: +375 29 337 14 12")
    print()
    if platform.system() == "Windows":
        try:
            ans = input("Запустить CSL-Tools сейчас? (Y/n): ").strip().lower()
            if ans in ("", "y", "д", "yes"):
                exe_path = install_dir / "CSL-Tools.exe"
                if exe_path.exists():
                    os.startfile(str(exe_path))
                else:
                    subprocess.Popen([sys.executable, str(src_dir / "main.py")])
        except:
            pass

if __name__ == "__main__":
    install()
