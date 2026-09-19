#!/usr/bin/env python3
# CSL-Tools Console version for Windows single exe without tkinter
import os, sys, platform, socket, subprocess, datetime, json
from pathlib import Path

def run_cmd(cmd, shell=False, timeout=15):
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='ignore')
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return f"Error: {e}", 1

def check_internet():
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3).close()
        return True
    except:
        return False

def main():
    print("="*70)
    print("CSL-Tools v1.6.0 - Консольная диагностика")
    print("ООО «Компьютерная безопасность» | csl.by | admin@csl.by")
    print("Минск, Фабрициуса 9 | +375 29 337 14 12")
    print("="*70)
    print(f"Дата: {datetime.datetime.now()}")
    print(f"OS: {platform.system()} {platform.release()} {platform.version()}")
    print(f"Hostname: {socket.gethostname()}")
    try:
        print(f"IP: {socket.gethostbyname(socket.gethostname())}")
    except:
        pass
    print()

    # Internet
    print("[1] Проверка интернета...")
    internet = check_internet()
    print(f"    Интернет: {'OK' if internet else 'НЕТ'}")

    # ipconfig
    print("\n[2] Сетевые адаптеры:")
    if platform.system() == "Windows":
        out, _ = run_cmd("ipconfig /all", shell=True)
        print(out[:4000])
    else:
        out, _ = run_cmd("ip addr show", shell=True)
        print(out[:4000])

    # VPN/Proxy
    print("\n[3] VPN/Прокси:")
    if platform.system() == "Windows":
        out, _ = run_cmd('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable', shell=True)
        print(out)
        out2, _ = run_cmd("netsh winhttp show proxy", shell=True)
        print(out2)

    # DNS
    print("\n[4] DNS:")
    try:
        ip = socket.gethostbyname("csl.by")
        print(f"    csl.by -> {ip} OK")
    except Exception as e:
        print(f"    csl.by FAIL: {e}")
    try:
        ip = socket.gethostbyname("google.com")
        print(f"    google.com -> {ip} OK")
    except Exception as e:
        print(f"    google.com FAIL: {e}")

    # Ping
    print("\n[5] Пинг:")
    hosts = ["8.8.8.8", "1.1.1.1", "google.com", "csl.by"]
    for h in hosts:
        if platform.system() == "Windows":
            out, _ = run_cmd(f"ping -n 2 {h}", shell=True, timeout=10)
        else:
            out, _ = run_cmd(f"ping -c 2 {h}", shell=True, timeout=10)
        ok = "TTL" in out or "ttl" in out.lower()
        print(f"    {h}: {'OK' if ok else 'FAIL'}")

    # BSOD
    print("\n[6] BlueScreen:")
    if platform.system() == "Windows":
        minidump = Path("C:/Windows/Minidump")
        if minidump.exists():
            files = list(minidump.glob("*.dmp"))[:5]
            print(f"    Найдено дампов: {len(files)}")
            for f in files:
                print(f"      {f.name}")
        else:
            print("    Папка Minidump не найдена")
    else:
        print("    Только для Windows")

    # Save report
    print("\n" + "="*70)
    report = f"CSL-Tools Report {datetime.datetime.now()}\n"
    report += f"Host: {socket.gethostname()}\n"
    report += f"Internet: {internet}\n"
    report += f"OS: {platform.system()} {platform.release()}\n"

    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home() / "Рабочий стол"
    if not desktop.exists():
        desktop = Path.cwd()
    report_path = desktop / f"CSL-Tools_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
            f.write("\nДля отправки на admin@csl.by прикрепите этот файл к письму\n")
        print(f"Отчет сохранен: {report_path}")
    except Exception as e:
        print(f"Не удалось сохранить отчет: {e}")

    print("\nДля поддержки: admin@csl.by / +375 29 337 14 12 / csl.by")
    print("="*70)
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
