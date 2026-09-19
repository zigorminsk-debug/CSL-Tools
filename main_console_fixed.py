#!/usr/bin/env python3
# CSL-Tools Console FIXED - не схлопывается
import os, sys, platform, socket, subprocess, datetime, traceback
from pathlib import Path

def log_error(msg):
    try:
        log_path = Path(os.environ.get('TEMP', '.')) / "CSL-Tools-error.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{datetime.datetime.now()} - {msg}\n")
            f.write(traceback.format_exc() + "\n")
    except:
        pass

def run_cmd(cmd, shell=False, timeout=15):
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='ignore')
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return f"Error: {e}", 1

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3).close()
        return True
    except:
        return False

def main():
    try:
        print("="*70, flush=True)
        print("CSL-Tools v1.6.1 - Консольная диагностика (FIXED)", flush=True)
        print("ООО «Компьютерная безопасность» | csl.by | admin@csl.by", flush=True)
        print("="*70, flush=True)
        print(f"Дата: {datetime.datetime.now()}", flush=True)
        print(f"OS: {platform.system()} {platform.release()} {platform.version()}", flush=True)
        print(f"Python: {platform.python_version()}", flush=True)
        print(f"Exe: {sys.executable}", flush=True)
        print(f"Argv: {sys.argv}", flush=True)
        try:
            print(f"Hostname: {socket.gethostname()}", flush=True)
            print(f"IP: {socket.gethostbyname(socket.gethostname())}", flush=True)
        except Exception as e:
            print(f"Hostname error: {e}", flush=True)
        print(flush=True)

        # Internet
        print("[1] Проверка интернета...", flush=True)
        internet = check_internet()
        print(f"    Интернет: {'OK' if internet else 'НЕТ'}", flush=True)

        # ipconfig
        print("\n[2] Сетевые адаптеры:", flush=True)
        if platform.system() == "Windows":
            out, _ = run_cmd("ipconfig /all", shell=True)
            print(out[:5000], flush=True)
        else:
            out, _ = run_cmd("ip addr show", shell=True)
            print(out[:5000], flush=True)

        # VPN/Proxy
        print("\n[3] VPN/Прокси:", flush=True)
        if platform.system() == "Windows":
            try:
                out, _ = run_cmd('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable', shell=True)
                print(out, flush=True)
                out2, _ = run_cmd("netsh winhttp show proxy", shell=True)
                print(out2, flush=True)
            except Exception as e:
                print(f"  Ошибка: {e}", flush=True)
                log_error(f"VPN/Proxy: {e}")

        # DNS
        print("\n[4] DNS:", flush=True)
        try:
            ip = socket.gethostbyname("csl.by")
            print(f"    csl.by -> {ip} OK", flush=True)
        except Exception as e:
            print(f"    csl.by FAIL: {e}", flush=True)
        try:
            ip = socket.gethostbyname("google.com")
            print(f"    google.com -> {ip} OK", flush=True)
        except Exception as e:
            print(f"    google.com FAIL: {e}", flush=True)

        # Ping
        print("\n[5] Пинг:", flush=True)
        hosts = ["8.8.8.8", "1.1.1.1", "google.com", "csl.by"]
        for h in hosts:
            try:
                if platform.system() == "Windows":
                    out, _ = run_cmd(f"ping -n 2 {h}", shell=True, timeout=10)
                else:
                    out, _ = run_cmd(f"ping -c 2 {h}", shell=True, timeout=10)
                ok = "TTL" in out or "ttl" in out.lower()
                print(f"    {h}: {'OK' if ok else 'FAIL'}", flush=True)
                if not ok:
                    print(f"      {out[:200]}", flush=True)
            except Exception as e:
                print(f"    {h}: ERROR {e}", flush=True)
                log_error(f"Ping {h}: {e}")

        # BSOD
        print("\n[6] BlueScreen:", flush=True)
        if platform.system() == "Windows":
            try:
                minidump = Path("C:/Windows/Minidump")
                if minidump.exists():
                    files = list(minidump.glob("*.dmp"))[:5]
                    print(f"    Найдено дампов: {len(files)}", flush=True)
                    for f in files:
                        print(f"      {f.name}", flush=True)
                else:
                    print("    Папка Minidump не найдена", flush=True)
            except Exception as e:
                print(f"    Ошибка BSOD: {e}", flush=True)
                log_error(f"BSOD: {e}")
        else:
            print("    Только для Windows", flush=True)

        # Save report
        print("\n" + "="*70, flush=True)
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "Рабочий стол"
        if not desktop.exists():
            desktop = Path.cwd()
        report_path = desktop / f"CSL-Tools_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"CSL-Tools Report {datetime.datetime.now()}\n")
                f.write(f"Host: {socket.gethostname()}\n")
                f.write(f"Internet: {internet}\n")
            print(f"Отчет сохранен: {report_path}", flush=True)
        except Exception as e:
            print(f"Не удалось сохранить отчет: {e}", flush=True)
            log_error(f"Save report: {e}")

        print("\nДля поддержки: admin@csl.by / +375 29 337 14 12 / csl.by", flush=True)
        print("="*70, flush=True)

    except Exception as e:
        print(f"\n[КРИТИЧЕСКАЯ ОШИБКА] {e}", flush=True)
        traceback.print_exc()
        log_error(f"Critical: {e}")
        try:
            # Попытка показать MessageBox на Windows
            if platform.system() == "Windows":
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, f"CSL-Tools ошибка:\n{e}\n\nЛог: %TEMP%\\CSL-Tools-error.log", "CSL-Tools Error", 0x10)
        except:
            pass

    finally:
        print("\n" + "="*70, flush=True)
        print("Диагностика завершена.", flush=True)
        print("Окно НЕ закроется автоматически. Нажмите Enter для выхода...", flush=True)
        print("="*70, flush=True)
        try:
            input()
        except:
            try:
                # Если input не работает (GUI exe), ждем через os.system pause
                if platform.system() == "Windows":
                    os.system("pause")
                else:
                    import time
                    time.sleep(10)
            except:
                pass

if __name__ == "__main__":
    main()
