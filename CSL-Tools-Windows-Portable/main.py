#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSL-Tools v1.6.0 - Сетевая диагностика
Разработано для ООО «Компьютерная безопасность» | csl.by
Минск, ул. Фабрициуса 9 | +375 29 337 14 12 | admin@csl.by / info@csl.by
Новое: отправка отчета на admin@csl.by + инсталлятор
"""

import os
import sys
import re
import socket
import platform
import subprocess
import threading
import datetime
import json
import shutil
import ipaddress
import smtplib
import ssl
import webbrowser
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
except ImportError:
    tk = None

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# --- Константы стиля CSL.by ---
CSL_ORANGE = "#FF7A00"
CSL_ORANGE_DARK = "#E56E00"
CSL_ORANGE_LIGHT = "#FFF0E0"
CSL_DARK = "#1F1F1F"
CSL_GRAY_BG = "#F7F7F8"
CSL_WHITE = "#FFFFFF"
CSL_TEXT = "#2B2B2B"
CSL_TEXT_LIGHT = "#6B7280"
CSL_BORDER = "#E5E7EB"
CSL_SUCCESS = "#10B981"
CSL_ERROR = "#EF4444"
CSL_WARN = "#F59E0B"

APP_NAME = "CSL-Tools"
APP_VERSION = "1.6.0"
COMPANY = "ООО «Компьютерная безопасность»"
SITE = "csl.by"
ADMIN_EMAIL = "admin@csl.by"
CONTACTS = {
    "address": "г. Минск, ул. Фабрициуса 9",
    "phone": "+375 29 337 14 12",
    "email": "info@csl.by",
    "admin_email": "admin@csl.by",
    "work": "Пн-Пт 9:00-17:00"
}

def is_windows():
    return platform.system() == "Windows"

def is_admin():
    if is_windows():
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        return os.geteuid() == 0

def get_config_dir():
    if is_windows():
        base = os.environ.get("APPDATA", str(Path.home()))
        return Path(base) / "CSL-Tools"
    else:
        return Path.home() / ".config" / "CSL-Tools"

def load_email_config():
    cfg_dir = get_config_dir()
    cfg_file = cfg_dir / "email_config.json"
    default = {
        "smtp_server": "mail.csl.by",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_pass": "",
        "use_tls": True,
        "from_email": "",
        "to_email": ADMIN_EMAIL,
        "client_name": "",
        "client_phone": ""
    }
    try:
        if cfg_file.exists():
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                default.update(data)
    except:
        pass
    return default

def save_email_config(cfg):
    try:
        cfg_dir = get_config_dir()
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "email_config.json"
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Save config error: {e}")
        return False

def send_email_smtp(to_email, subject, body, attachment_path=None, smtp_config=None):
    """Отправка через SMTP"""
    if smtp_config is None:
        smtp_config = load_email_config()
    
    smtp_server = smtp_config.get("smtp_server", "")
    smtp_port = int(smtp_config.get("smtp_port", 587))
    smtp_user = smtp_config.get("smtp_user", "")
    smtp_pass = smtp_config.get("smtp_pass", "")
    from_email = smtp_config.get("from_email") or smtp_user or "csl-tools@csl.by"
    use_tls = smtp_config.get("use_tls", True)

    if not smtp_server or not smtp_user:
        raise ValueError("Не настроен SMTP сервер / логин. Откройте Настройки SMTP.")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    if attachment_path and Path(attachment_path).exists():
        try:
            with open(attachment_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{Path(attachment_path).name}"')
            msg.attach(part)
        except Exception as e:
            body += f"\n\n[Ошибка прикрепления файла: {e}]"

    context = ssl.create_default_context()
    # Try TLS
    if use_tls:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
            server.ehlo()
            try:
                server.starttls(context=context)
                server.ehlo()
            except:
                pass
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    else:
        # SSL
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=15) as server:
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
    return True

def send_via_powershell(to_email, subject, body, attachment_path=None):
    """Альтернативная отправка через PowerShell (если SMTP заблокирован, но есть Outlook)"""
    if not is_windows():
        return False, "PowerShell доступен только на Windows"
    # Экранируем
    body_esc = body.replace("'", "''").replace('"', '`"')[:4000]
    subject_esc = subject.replace("'", "''")
    ps_script = f"""
    try {{
        $Outlook = New-Object -ComObject Outlook.Application -ErrorAction Stop
        $Mail = $Outlook.CreateItem(0)
        $Mail.To = "{to_email}"
        $Mail.Subject = "{subject_esc}"
        $Mail.Body = @'
{body}
'@
        if ("{attachment_path}" -ne "" -and (Test-Path "{attachment_path}")) {{
            $Mail.Attachments.Add("{attachment_path}")
        }}
        $Mail.Display()
        Write-Output "Outlook opened"
    }} catch {{
        Write-Output "Outlook error: $($_.Exception.Message)"
        # Fallback mailto
        $mailto = "mailto:{to_email}?subject={subject_esc}&body=$([uri]::EscapeDataString('{body_esc}'))"
        Start-Process $mailto
        Write-Output "mailto opened"
    }}
    """
    out, code = run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=15)
    return code == 0, out

def open_mailto(to_email, subject, body):
    """Открыть почтовый клиент по умолчанию"""
    import urllib.parse
    subject_enc = urllib.parse.quote(subject)
    body_enc = urllib.parse.quote(body[:1500])  # mailto ограничение
    url = f"mailto:{to_email}?subject={subject_enc}&body={body_enc}"
    try:
        webbrowser.open(url)
        if is_windows():
            os.startfile(url)
        return True
    except Exception as e:
        try:
            webbrowser.open(url)
            return True
        except:
            return False

def run_cmd(cmd, shell=False, timeout=15):
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='ignore'
        )
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "Таймаут выполнения команды", 1
    except Exception as e:
        return f"Ошибка: {e}", 1

def run_powershell(ps_cmd, timeout=20):
    if is_windows():
        cmd = ["powershell", "-NoProfile", "-Command", ps_cmd]
    else:
        return run_cmd(ps_cmd, shell=True, timeout=timeout)
    return run_cmd(cmd, timeout=timeout)

# ================== ДИАГНОСТИЧЕСКИЕ ФУНКЦИИ ==================

def get_network_adapters_info():
    out = {}
    if is_windows():
        ip_out, _ = run_cmd("ipconfig /all", shell=True, timeout=10)
        out['ipconfig'] = ip_out
        ps_out, _ = run_cmd(["powershell", "-Command",
            "Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,LinkSpeed,MediaConnectionState | Format-List | Out-String -Width 200"],
            timeout=10)
        out['adapters'] = ps_out
        ps_ip, _ = run_cmd(["powershell", "-Command",
            "Get-NetIPConfiguration | Format-List | Out-String -Width 300"],
            timeout=10)
        out['ipconfig_ps'] = ps_ip
        netsh_out, _ = run_cmd("netsh interface ip show config", shell=True, timeout=10)
        out['netsh'] = netsh_out
    else:
        ip_a, _ = run_cmd("ip addr show", shell=True)
        out['ipconfig'] = ip_a
        route, _ = run_cmd("ip route show", shell=True)
        out['netsh'] = route
        out['adapters'] = ip_a
        out['ipconfig_ps'] = ""
    return out

def check_vpn_proxy():
    result = {"vpn": [], "proxy": [], "details": ""}
    details = []
    adapters = get_network_adapters_info()
    ipconfig_text = adapters.get('ipconfig','') + adapters.get('adapters','')
    vpn_keywords = ["TAP", "TUN", "VPN", "WireGuard", "OpenVPN", "Nord", "ExpressVPN", "L2TP", "PPTP", "SSTP", "IKEv2", "ZeroTier", "Hamachi", "Radmin"]
    found_vpn = []
    for kw in vpn_keywords:
        if kw.lower() in ipconfig_text.lower():
            for line in ipconfig_text.splitlines():
                if kw.lower() in line.lower():
                    found_vpn.append(line.strip())
    if is_windows():
        tasklist, _ = run_cmd('tasklist', shell=True, timeout=8)
        vpn_processes = ["openvpn", "wireguard", "nordvpn", "expressvpn", "windscribe", "protonvpn", "softether", "hamachi", "zerotier", "forticlient", "anyconnect"]
        for vp in vpn_processes:
            if vp.lower() in tasklist.lower():
                found_vpn.append(f"Процесс: {vp} обнаружен в tasklist")
        route_out, _ = run_cmd("route print", shell=True, timeout=8)
        if "0.0.0.0" in route_out:
            details.append("Таблица маршрутов:\n" + "\n".join(route_out.splitlines()[:60]))
    else:
        ps_out, _ = run_cmd("ps aux | grep -i vpn", shell=True)
        if "vpn" in ps_out.lower():
            found_vpn.append(ps_out.strip()[:200])
    result["vpn"] = list(dict.fromkeys(found_vpn))
    proxy_found = []
    if is_windows():
        reg_out, _ = run_cmd('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable', shell=True)
        details.append(f"ProxyEnable Registry: {reg_out.strip()}")
        if "0x1" in reg_out:
            proxy_found.append("Системный прокси включен (ProxyEnable=1)")
        reg_server, _ = run_cmd('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer', shell=True)
        if "ProxyServer" in reg_server:
            proxy_found.append(f"ProxyServer: {reg_server.strip()}")
            details.append(reg_server)
        winhttp, _ = run_cmd("netsh winhttp show proxy", shell=True)
        details.append(f"netsh winhttp:\n{winhttp}")
        if "Прямой доступ" not in winhttp and "Direct access" not in winhttp and winhttp.strip():
            if "proxy" in winhttp.lower():
                proxy_found.append(f"WinHTTP proxy: {winhttp.strip()[:150]}")
        reg_pac, _ = run_cmd('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v AutoConfigURL', shell=True)
        if "AutoConfigURL" in reg_pac:
            proxy_found.append(f"PAC/WPAD: {reg_pac.strip()}")
    else:
        for env_var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy"]:
            val = os.environ.get(env_var)
            if val:
                proxy_found.append(f"{env_var}={val}")
    result["proxy"] = proxy_found
    result["details"] = "\n\n".join(details)
    return result

def ping_test(hosts=None, count=4):
    if hosts is None:
        hosts = ["8.8.8.8", "1.1.1.1", "77.88.8.8", "google.com", "csl.by"]
    results = {}
    for host in hosts:
        if is_windows():
            cmd = f"ping -n {count} {host}"
        else:
            cmd = f"ping -c {count} {host}"
        out, code = run_cmd(cmd, shell=True, timeout=12)
        results[host] = {"output": out, "success": code == 0 or "TTL" in out or "ttl" in out.lower()}
    return results

def traceroute_test(hosts=None):
    if hosts is None:
        hosts = ["8.8.8.8", "google.com", "csl.by"]
    results = {}
    for host in hosts:
        if is_windows():
            cmd = f"tracert -d -h 20 {host}"
        else:
            cmd = f"traceroute -n -m 20 {host} 2>&1 || tracepath -n {host} 2>&1"
        out, code = run_cmd(cmd, shell=True, timeout=25)
        results[host] = {"output": out, "success": code == 0}
    return results

def check_dns_dhcp():
    result = {"dns_servers": [], "dhcp_enabled": None, "resolution": {}, "nslookup": "", "details": ""}
    if is_windows():
        ip_out, _ = run_cmd("ipconfig /all", shell=True)
        result["details"] = ip_out[:5000]
        dns_lines = [l for l in ip_out.splitlines() if "DNS" in l and ":" in l]
        result["dns_servers"] = dns_lines[:10]
        if "DHCP Enabled" in ip_out or "DHCP включен" in ip_out:
            result["dhcp_enabled"] = "Yes" in ip_out or "Да" in ip_out
        ns_out, _ = run_cmd("nslookup csl.by 8.8.8.8", shell=True, timeout=10)
        result["nslookup"] = ns_out
        ps_dns, _ = run_cmd(["powershell", "-Command", "Get-DnsClientServerAddress | Format-List | Out-String -Width 200"], timeout=8)
        result["ps_dns"] = ps_dns
    else:
        try:
            with open("/etc/resolv.conf") as f:
                resolv = f.read()
                result["details"] = resolv
                for line in resolv.splitlines():
                    if "nameserver" in line:
                        result["dns_servers"].append(line.strip())
        except:
            pass
        ns_out, _ = run_cmd("nslookup csl.by 8.8.8.8", shell=True, timeout=10)
        result["nslookup"] = ns_out
    test_hosts = ["google.com", "csl.by", "ya.ru", "microsoft.com"]
    for h in test_hosts:
        try:
            ip = socket.gethostbyname(h)
            result["resolution"][h] = f"OK -> {ip}"
        except Exception as e:
            result["resolution"][h] = f"FAIL -> {e}"
    return result

def check_internet():
    result = {"connected": False, "tests": {}}
    tests = [
        ("8.8.8.8:53 TCP", lambda: socket.create_connection(("8.8.8.8", 53), timeout=3)),
        ("1.1.1.1:53 TCP", lambda: socket.create_connection(("1.1.1.1", 53), timeout=3)),
    ]
    if HAS_REQUESTS:
        def http_test(url):
            r = requests.get(url, timeout=5)
            return f"HTTP {r.status_code}"
        tests += [
            ("https://google.com", lambda: http_test("https://google.com")),
            ("https://csl.by", lambda: http_test("https://csl.by")),
            ("https://ya.ru", lambda: http_test("https://ya.ru")),
        ]
    else:
        tests += [
            ("google.com:80", lambda: socket.create_connection(("google.com", 80), timeout=4)),
            ("csl.by:443", lambda: socket.create_connection(("csl.by", 443), timeout=4)),
        ]
    for name, fn in tests:
        try:
            res = fn()
            if hasattr(res, 'close'):
                try:
                    res.close()
                except:
                    pass
            result["tests"][name] = f"OK {res if isinstance(res, str) else ''}"
            result["connected"] = True
        except Exception as e:
            result["tests"][name] = f"FAIL: {e}"
    return result

def analyze_bluescreen():
    result = {"minidumps": [], "memory_dump": False, "bugcheck_events": "", "summary": ""}
    if is_windows():
        minidump_path = Path("C:/Windows/Minidump")
        if minidump_path.exists():
            files = list(minidump_path.glob("*.dmp"))
            for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                try:
                    stat = f.stat()
                    result["minidumps"].append({
                        "name": f.name,
                        "path": str(f),
                        "size": stat.st_size,
                        "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
                except:
                    pass
        else:
            result["summary"] += "Папка Minidump не найдена. "
        mem_dump = Path("C:/Windows/MEMORY.DMP")
        result["memory_dump"] = mem_dump.exists()
        if result["memory_dump"]:
            try:
                size = mem_dump.stat().st_size
                result["summary"] += f"Найден MEMORY.DMP ({size//1024//1024} MB). "
            except:
                pass
        ps_cmd = """
        Get-WinEvent -FilterHashtable @{LogName='System'; ID=1001,41,1003} -MaxEvents 15 -ErrorAction SilentlyContinue | 
        ForEach-Object {
            $msg = $_.Message.Substring(0, [Math]::Min(500, $_.Message.Length))
            \"[$($_.TimeCreated)] ID=$($_.Id) Level=$($_.LevelDisplayName)`n$msg`n---\"
        } | Out-String -Width 400
        """
        out, _ = run_powershell(ps_cmd, timeout=15)
        result["bugcheck_events"] = out
        reg_out, _ = run_cmd('reg query "HKLM\\SYSTEM\\CurrentControlSet\\Control\\CrashControl" 2>&1', shell=True)
        result["crashcontrol"] = reg_out
        if not result["minidumps"] and "BugCheck" not in out:
            result["summary"] += "Критических ошибок (BSOD) за последнее время не обнаружено в журнале."
        else:
            result["summary"] += f"Найдено {len(result['minidumps'])} дампов. Проверьте журнал ниже."
    else:
        dmesg_out, _ = run_cmd("dmesg | grep -i -E 'panic|oops|bug|error' | tail -n 30", shell=True)
        result["bugcheck_events"] = dmesg_out
        result["summary"] = "Linux: проверка dmesg на паники ядра."
        crash_path = Path("/var/crash")
        if crash_path.exists():
            result["minidumps"] = [{"name": f.name, "path": str(f)} for f in crash_path.glob("*")][:10]
    return result

def fix_flush_dns():
    if is_windows():
        out1, _ = run_cmd("ipconfig /flushdns", shell=True)
        out2, _ = run_cmd("netsh winsock reset", shell=True)
        return out1 + "\n" + out2
    else:
        out, _ = run_cmd("sudo systemd-resolve --flush-caches; sudo resolvconf --flush-caches; echo flushed", shell=True)
        return out

def fix_release_renew():
    if is_windows():
        out1, _ = run_cmd("ipconfig /release", shell=True, timeout=10)
        out2, _ = run_cmd("ipconfig /renew", shell=True, timeout=20)
        return out1 + "\n" + out2
    else:
        out, _ = run_cmd("sudo dhclient -r; sudo dhclient", shell=True, timeout=15)
        return out

def fix_reset_ip():
    if is_windows():
        cmds = ["netsh int ip reset", "netsh winsock reset", "netsh advfirewall reset"]
        total = ""
        for c in cmds:
            o, _ = run_cmd(c, shell=True, timeout=10)
            total += f"\n> {c}\n{o}\n"
        return total
    else:
        return "Сброс IP доступен только на Windows"

def fix_disable_proxy():
    if is_windows():
        cmds = [
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f',
            'netsh winhttp reset proxy'
        ]
        total = ""
        for c in cmds:
            o, _ = run_cmd(c, shell=True)
            total += f"\n> {c}\n{o}\n"
        return total
    else:
        removed = []
        for k in list(os.environ.keys()):
            if "proxy" in k.lower():
                removed.append(k)
                del os.environ[k]
        return f"Удалены переменные окружения: {removed}"

def fix_set_dns_auto():
    if is_windows():
        ps = "Get-NetAdapter -Physical | Where-Object Status -eq 'Up' | Select-Object -First 1 -ExpandProperty Name"
        out, _ = run_powershell(ps, timeout=8)
        adapter = out.strip().splitlines()[0] if out.strip() else "Ethernet"
        cmds = [f'netsh interface ip set dns "{adapter}" dhcp']
        total = f"Адаптер: {adapter}\n"
        for c in cmds[:1]:
            o, _ = run_cmd(c, shell=True)
            total += f"{c}\n{o}\n"
        return total
    else:
        return "Установка DNS auto только на Windows"

def fix_restart_adapter():
    if is_windows():
        ps = """
        $adapters = Get-NetAdapter -Physical | Where-Object Status -eq 'Up'
        foreach ($a in $adapters) {
            Write-Output \"Перезапуск $($a.Name)...\"
            Restart-NetAdapter -Name $a.Name -Confirm:$false
            Start-Sleep -Seconds 2
            Write-Output \"OK\"
        }
        """
        out, _ = run_powershell(ps, timeout=20)
        return out
    else:
        out, _ = run_cmd("sudo ip link set $(ip route | grep default | awk '{print $5}' | head -n1) down; sleep 2; sudo ip link set $(ip route | grep default | awk '{print $5}' | head -n1) up; echo restarted", shell=True, timeout=10)
        return out

# ================== GUI ==================

class CSLToolsApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION} - {COMPANY} | {SITE} | Отправка на {ADMIN_EMAIL}")
        self.root.geometry("1220x820")
        self.root.minsize(1080, 720)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass
        style.configure("TButton", padding=8, font=("Segoe UI", 10))
        style.configure("Accent.TButton", background=CSL_ORANGE, foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", CSL_ORANGE_DARK)])
        style.configure("Header.TLabel", background=CSL_ORANGE, foreground="white", font=("Segoe UI", 14, "bold"))
        style.configure("TNotebook.Tab", padding=[15, 8], font=("Segoe UI", 10))

        self.create_header()
        main_container = tk.Frame(root, bg=CSL_GRAY_BG)
        main_container.pack(fill=tk.BOTH, expand=True)
        self.create_left_menu(main_container)
        right_frame = tk.Frame(main_container, bg=CSL_WHITE)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tabs = {}
        self.logs = {}
        self.email_config = load_email_config()
        self.last_report_path = None

        self.create_tab("dashboard", "📊  Дашборд", self.build_dashboard)
        self.create_tab("adapters", "🌐  Сетевые карты", self.build_adapters)
        self.create_tab("vpn", "🔒  VPN / Прокси", self.build_vpn)
        self.create_tab("ping", "📡  Пинг / Трассировка", self.build_ping)
        self.create_tab("dns", "🔍  DNS / DHCP / Интернет", self.build_dns)
        self.create_tab("fix", "🛠  Исправление", self.build_fix)
        self.create_tab("bsod", "💀  BlueScreen", self.build_bsod)
        self.create_tab("report", "📄  Отчет + Email", self.build_report)

        self.create_status_bar()
        self.root.after(500, lambda: self.run_auto_diagnostics())

    def create_header(self):
        header = tk.Frame(self.root, bg=CSL_ORANGE, height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        left = tk.Frame(header, bg=CSL_ORANGE)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=8)
        tk.Label(left, text="CSL-TOOLS", font=("Segoe UI", 20, "bold"), bg=CSL_ORANGE, fg="white").pack(anchor="w")
        tk.Label(left, text=f"Сетевая диагностика • {COMPANY} • {SITE} • {ADMIN_EMAIL}", font=("Segoe UI", 10), bg=CSL_ORANGE, fg="#FFE5CC").pack(anchor="w")
        right = tk.Frame(header, bg=CSL_ORANGE)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=5)
        contacts_text = f"{CONTACTS['address']} | {CONTACTS['phone']} | {ADMIN_EMAIL} | {CONTACTS['work']}"
        tk.Label(right, text=contacts_text, font=("Segoe UI", 9), bg=CSL_ORANGE, fg="white", justify=tk.RIGHT).pack(anchor="e")
        tk.Label(right, text="10 лет • 160 серверов • 80 клиентов • Мгновенная помощь", font=("Segoe UI", 8, "bold"), bg=CSL_ORANGE, fg="#FFD8B0").pack(anchor="e", pady=(4,0))
        admin_text = "✔ Запущено от Администратора" if is_admin() else "⚠ Запустите от Администратора"
        admin_color = "#C6F6D5" if is_admin() else "#FEE2E2"
        tk.Label(right, text=admin_text, font=("Segoe UI", 8), bg=CSL_ORANGE, fg=admin_color).pack(anchor="e")

    def create_left_menu(self, parent):
        menu = tk.Frame(parent, bg=CSL_DARK, width=210)
        menu.pack(side=tk.LEFT, fill=tk.Y)
        menu.pack_propagate(False)
        tk.Label(menu, text="НАВИГАЦИЯ", font=("Segoe UI", 9, "bold"), bg=CSL_DARK, fg="#9CA3AF", anchor="w").pack(fill=tk.X, padx=15, pady=(15,5))
        buttons = [
            ("📊 Дашборд", "dashboard"),
            ("🌐 Адаптеры", "adapters"),
            ("🔒 VPN/Прокси", "vpn"),
            ("📡 Пинг/Трейс", "ping"),
            ("🔍 DNS/DHCP", "dns"),
            ("🛠 Исправление", "fix"),
            ("💀 BlueScreen", "bsod"),
            ("📄 Отчет + Email", "report"),
        ]
        self.menu_buttons = {}
        for label, key in buttons:
            btn = tk.Button(menu, text=label, font=("Segoe UI", 10), bg=CSL_DARK, fg="white",
                            activebackground="#2D2D2D", activeforeground=CSL_ORANGE,
                            bd=0, anchor="w", padx=15, pady=10,
                            command=lambda k=key: self.switch_tab(k))
            btn.pack(fill=tk.X, padx=5, pady=1)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#2D2D2D"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=CSL_DARK))
            self.menu_buttons[key] = btn
        tk.Label(menu, text="", bg=CSL_DARK).pack(fill=tk.BOTH, expand=True)
        help_btn = tk.Button(menu, text=f"🆘 Нужна помощь?\n{CONTACTS['phone']}\n{ADMIN_EMAIL}", font=("Segoe UI", 9, "bold"),
                             bg=CSL_ORANGE, fg="white", bd=0, padx=10, pady=12,
                             command=lambda: messagebox.showinfo("Помощь CSL", f"{COMPANY}\n{SITE}\n\n{CONTACTS['address']}\n{CONTACTS['phone']}\n{ADMIN_EMAIL}\n\nВремя работы: {CONTACTS['work']}\n\nНажмите для удаленной поддержки!"))
        help_btn.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(menu, text=f"{APP_NAME} v{APP_VERSION}\n© csl.by\nОтправка: {ADMIN_EMAIL}", font=("Segoe UI", 7), bg=CSL_DARK, fg="#6B7280", justify=tk.LEFT).pack(fill=tk.X, padx=15, pady=5)

    def create_tab(self, key, title, builder):
        frame = tk.Frame(self.notebook, bg=CSL_WHITE)
        self.notebook.add(frame, text=title)
        self.tabs[key] = frame
        builder(frame)

    def switch_tab(self, key):
        if key in self.tabs:
            self.notebook.select(self.tabs[key])
            for k, btn in self.menu_buttons.items():
                if k == key:
                    btn.config(bg=CSL_ORANGE, fg="white")
                else:
                    btn.config(bg=CSL_DARK, fg="white")

    def create_status_bar(self):
        status = tk.Frame(self.root, bg="#F3F4F6", height=28)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)
        self.status_label = tk.Label(status, text=f"Готов | {APP_NAME} {APP_VERSION} | Отправка на {ADMIN_EMAIL}", font=("Segoe UI", 9), bg="#F3F4F6", fg=CSL_TEXT_LIGHT, anchor="w")
        self.status_label.pack(side=tk.LEFT, padx=10)
        tk.Label(status, text=f"OS: {platform.system()} {platform.release()} | Python {platform.python_version()} | {datetime.datetime.now().strftime('%d.%m.%Y')}", font=("Segoe UI", 8), bg="#F3F4F6", fg=CSL_TEXT_LIGHT).pack(side=tk.RIGHT, padx=10)

    def set_status(self, text):
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def log(self, tab_key, text):
        if tab_key in self.logs:
            widget = self.logs[tab_key]
            widget.config(state=tk.NORMAL)
            widget.insert(tk.END, text + "\n")
            widget.see(tk.END)
            widget.config(state=tk.DISABLED)

    def clear_log(self, tab_key):
        if tab_key in self.logs:
            w = self.logs[tab_key]
            w.config(state=tk.NORMAL)
            w.delete(1.0, tk.END)
            w.config(state=tk.DISABLED)

    def threaded(self, func, *args, **kwargs):
        def wrapper():
            try:
                func(*args, **kwargs)
            except Exception as e:
                self.set_status(f"Ошибка: {e}")
        t = threading.Thread(target=wrapper, daemon=True)
        t.start()

    # ============ BUILDERS ============

    def build_dashboard(self, parent):
        top = tk.Frame(parent, bg=CSL_WHITE)
        top.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(top, text="Авто-диагностика сети", font=("Segoe UI", 14, "bold"), bg=CSL_WHITE, fg=CSL_TEXT).pack(anchor="w")
        tk.Label(top, text=f"Одним кликом проверит все компоненты и отправит отчет на {ADMIN_EMAIL}", font=("Segoe UI", 10), bg=CSL_WHITE, fg=CSL_TEXT_LIGHT).pack(anchor="w")
        btn_frame = tk.Frame(top, bg=CSL_WHITE)
        btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(btn_frame, text="▶ Запустить полную диагностику", bg=CSL_ORANGE, fg="white", font=("Segoe UI", 11, "bold"),
                  bd=0, padx=20, pady=10, command=lambda: self.threaded(self.run_auto_diagnostics)).pack(side=tk.LEFT, padx=(0,10))
        tk.Button(btn_frame, text="💾 Сохранить отчет", bg="#374151", fg="white", font=("Segoe UI", 10),
                  bd=0, padx=15, pady=10, command=self.save_report).pack(side=tk.LEFT)
        tk.Button(btn_frame, text=f"📧 Отправить на {ADMIN_EMAIL}", bg="#10B981", fg="white", font=("Segoe UI", 10, "bold"),
                  bd=0, padx=15, pady=10, command=lambda: self.threaded(self.send_report_email_quick)).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="🔄 Очистить", bg="#E5E7EB", fg=CSL_TEXT, font=("Segoe UI", 10),
                  bd=0, padx=15, pady=10, command=lambda: self.clear_log("dashboard")).pack(side=tk.LEFT, padx=5)

        cards_frame = tk.Frame(parent, bg=CSL_GRAY_BG)
        cards_frame.pack(fill=tk.X, padx=15, pady=5)
        self.dashboard_cards = {}
        statuses = [
            ("internet", "Интернет", "—"),
            ("adapters", "Адаптеры", "—"),
            ("vpn", "VPN/Прокси", "—"),
            ("dns", "DNS/DHCP", "—"),
            ("ping", "Пинг", "—"),
            ("bsod", "BSOD", "—"),
        ]
        for i, (key, title, val) in enumerate(statuses):
            card = tk.Frame(cards_frame, bg=CSL_WHITE, bd=1, relief=tk.SOLID, highlightbackground=CSL_BORDER)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            cards_frame.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=title, font=("Segoe UI", 9, "bold"), bg=CSL_WHITE, fg=CSL_TEXT_LIGHT).pack(anchor="w", padx=10, pady=(8,0))
            lbl = tk.Label(card, text=val, font=("Segoe UI", 12, "bold"), bg=CSL_WHITE, fg=CSL_TEXT)
            lbl.pack(anchor="w", padx=10, pady=(0,8))
            self.dashboard_cards[key] = lbl

        log_frame = tk.Frame(parent, bg=CSL_WHITE)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        txt = scrolledtext.ScrolledText(log_frame, font=("Consolas", 10), bg="#1E1E1E", fg="#D4D4D4", insertbackground="white")
        txt.pack(fill=tk.BOTH, expand=True)
        txt.config(state=tk.DISABLED)
        self.logs["dashboard"] = txt

    def build_adapters(self, parent):
        ctrl = tk.Frame(parent, bg=CSL_WHITE)
        ctrl.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(ctrl, text="Сетевые адаптеры и конфигурация", font=("Segoe UI", 13, "bold"), bg=CSL_WHITE).pack(anchor="w")
        tk.Button(ctrl, text="🔄 Обновить", bg=CSL_ORANGE, fg="white", bd=0, padx=15, pady=6,
                  command=lambda: self.threaded(self.refresh_adapters)).pack(anchor="w", pady=5)
        txt = scrolledtext.ScrolledText(parent, font=("Consolas", 10), bg=CSL_WHITE, fg=CSL_TEXT)
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,15))
        txt.config(state=tk.DISABLED)
        self.logs["adapters"] = txt

    def build_vpn(self, parent):
        ctrl = tk.Frame(parent, bg=CSL_WHITE)
        ctrl.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(ctrl, text="Проверка VPN и Прокси", font=("Segoe UI", 13, "bold"), bg=CSL_WHITE).pack(anchor="w")
        tk.Button(ctrl, text="🔍 Проверить VPN/Прокси", bg=CSL_ORANGE, fg="white", bd=0, padx=15, pady=6,
                  command=lambda: self.threaded(self.refresh_vpn)).pack(anchor="w", pady=5)
        txt = scrolledtext.ScrolledText(parent, font=("Consolas", 10), bg=CSL_WHITE)
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,15))
        txt.config(state=tk.DISABLED)
        self.logs["vpn"] = txt

    def build_ping(self, parent):
        ctrl = tk.Frame(parent, bg=CSL_WHITE)
        ctrl.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(ctrl, text="Пинг и Трассировка", font=("Segoe UI", 13, "bold"), bg=CSL_WHITE).pack(anchor="w")
        entry_frame = tk.Frame(ctrl, bg=CSL_WHITE)
        entry_frame.pack(fill=tk.X, pady=5)
        tk.Label(entry_frame, text="Хосты:", bg=CSL_WHITE).pack(side=tk.LEFT)
        self.ping_entry = tk.Entry(entry_frame, font=("Segoe UI", 10), width=50)
        self.ping_entry.insert(0, "8.8.8.8, 1.1.1.1, google.com, csl.by")
        self.ping_entry.pack(side=tk.LEFT, padx=10)
        btns = tk.Frame(ctrl, bg=CSL_WHITE)
        btns.pack(fill=tk.X, pady=5)
        tk.Button(btns, text="📡 Пинг", bg=CSL_ORANGE, fg="white", bd=0, padx=15, pady=6,
                  command=lambda: self.threaded(self.do_ping)).pack(side=tk.LEFT, padx=(0,5))
        tk.Button(btns, text="🛣 Трассировка", bg="#374151", fg="white", bd=0, padx=15, pady=6,
                  command=lambda: self.threaded(self.do_traceroute)).pack(side=tk.LEFT)
        txt = scrolledtext.ScrolledText(parent, font=("Consolas", 10), bg="#0F172A", fg="#E2E8F0")
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,15))
        txt.config(state=tk.DISABLED)
        self.logs["ping"] = txt

    def build_dns(self, parent):
        ctrl = tk.Frame(parent, bg=CSL_WHITE)
        ctrl.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(ctrl, text="DNS / DHCP / Интернет", font=("Segoe UI", 13, "bold"), bg=CSL_WHITE).pack(anchor="w")
        tk.Button(ctrl, text="🔍 Проверить DNS/DHCP", bg=CSL_ORANGE, fg="white", bd=0, padx=15, pady=6,
                  command=lambda: self.threaded(self.refresh_dns)).pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl, text="🌍 Проверить Интернет", bg="#374151", fg="white", bd=0, padx=15, pady=6,
                  command=lambda: self.threaded(self.refresh_internet)).pack(side=tk.LEFT)
        txt = scrolledtext.ScrolledText(parent, font=("Consolas", 10), bg=CSL_WHITE)
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,15))
        txt.config(state=tk.DISABLED)
        self.logs["dns"] = txt

    def build_fix(self, parent):
        ctrl = tk.Frame(parent, bg=CSL_WHITE)
        ctrl.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(ctrl, text="Исправление ошибок и сброс сети", font=("Segoe UI", 13, "bold"), bg=CSL_WHITE).pack(anchor="w")
        tk.Label(ctrl, text="⚠ Требуются права Администратора", font=("Segoe UI", 9, "bold"), bg=CSL_WHITE, fg=CSL_ERROR).pack(anchor="w")
        grid = tk.Frame(ctrl, bg=CSL_WHITE)
        grid.pack(fill=tk.X, pady=10)
        fixes = [
            ("🧹 Очистить DNS кеш", self.fix_dns),
            ("🔄 Release/Renew IP", self.fix_renew),
            ("♻ Сбросить Winsock/IP", self.fix_reset),
            ("🚫 Отключить Прокси", self.fix_proxy),
            ("🌐 DNS Авто / Google", self.fix_dns_auto),
            ("🔌 Перезапустить адаптер", self.fix_adapter),
            ("🔥 Полный сброс сети", self.fix_full),
        ]
        for i, (label, cmd) in enumerate(fixes):
            r = i // 3
            c = i % 3
            tk.Button(grid, text=label, bg=CSL_WHITE, fg=CSL_TEXT, bd=1, relief=tk.SOLID,
                      font=("Segoe UI", 10), padx=12, pady=8, width=22,
                      command=lambda fn=cmd: self.threaded(fn)).grid(row=r, column=c, padx=5, pady=5, sticky="ew")
        txt = scrolledtext.ScrolledText(parent, font=("Consolas", 10), bg="#1E1E1E", fg="#A7F3D0")
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,15))
        txt.config(state=tk.DISABLED)
        self.logs["fix"] = txt

    def build_bsod(self, parent):
        ctrl = tk.Frame(parent, bg=CSL_WHITE)
        ctrl.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(ctrl, text="Анализ BlueScreen (BSOD)", font=("Segoe UI", 13, "bold"), bg=CSL_WHITE).pack(anchor="w")
        btns = tk.Frame(ctrl, bg=CSL_WHITE)
        btns.pack(fill=tk.X, pady=5)
        tk.Button(btns, text="💀 Прочитать BSOD", bg=CSL_ORANGE, fg="white", bd=0, padx=15, pady=6,
                  command=lambda: self.threaded(self.refresh_bsod)).pack(side=tk.LEFT, padx=(0,5))
        tk.Button(btns, text="📂 Открыть папку Minidump", bg="#E5E7EB", bd=0, padx=10, pady=6,
                  command=self.open_minidump).pack(side=tk.LEFT)
        txt = scrolledtext.ScrolledText(parent, font=("Consolas", 10), bg="#1E1B4B", fg="#DDD6FE")
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,15))
        txt.config(state=tk.DISABLED)
        self.logs["bsod"] = txt

    def build_report(self, parent):
        # Верхняя панель управления отчетом
        ctrl = tk.Frame(parent, bg=CSL_WHITE)
        ctrl.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(ctrl, text="Итоговый отчет и отправка", font=("Segoe UI", 13, "bold"), bg=CSL_WHITE).pack(anchor="w")
        
        # Поля клиента
        client_frame = tk.Frame(ctrl, bg=CSL_ORANGE_LIGHT, bd=1, relief=tk.SOLID)
        client_frame.pack(fill=tk.X, pady=8, padx=0)

        tk.Label(client_frame, text="Данные для отправки в CSL:", font=("Segoe UI", 9, "bold"), bg=CSL_ORANGE_LIGHT).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(6,2))

        tk.Label(client_frame, text="Организация / ФИО:", font=("Segoe UI", 9), bg=CSL_ORANGE_LIGHT).grid(row=1, column=0, sticky="e", padx=10, pady=3)
        self.client_name_entry = tk.Entry(client_frame, font=("Segoe UI", 9), width=28)
        self.client_name_entry.insert(0, self.email_config.get("client_name",""))
        self.client_name_entry.grid(row=1, column=1, padx=5, pady=3, sticky="w")

        tk.Label(client_frame, text="Телефон:", font=("Segoe UI", 9), bg=CSL_ORANGE_LIGHT).grid(row=1, column=2, sticky="e", padx=10, pady=3)
        self.client_phone_entry = tk.Entry(client_frame, font=("Segoe UI", 9), width=20)
        self.client_phone_entry.insert(0, self.email_config.get("client_phone",""))
        self.client_phone_entry.grid(row=1, column=3, padx=5, pady=3, sticky="w")

        tk.Label(client_frame, text="Компьютер:", font=("Segoe UI", 9), bg=CSL_ORANGE_LIGHT).grid(row=2, column=0, sticky="e", padx=10, pady=3)
        self.pc_name_label = tk.Label(client_frame, text=socket.gethostname(), font=("Segoe UI", 9, "bold"), bg=CSL_ORANGE_LIGHT)
        self.pc_name_label.grid(row=2, column=1, sticky="w", padx=5, pady=3)

        tk.Label(client_frame, text="Отправить на:", font=("Segoe UI", 9), bg=CSL_ORANGE_LIGHT).grid(row=2, column=2, sticky="e", padx=10, pady=3)
        self.to_email_entry = tk.Entry(client_frame, font=("Segoe UI", 9, "bold"), width=20)
        self.to_email_entry.insert(0, self.email_config.get("to_email", ADMIN_EMAIL))
        self.to_email_entry.grid(row=2, column=3, padx=5, pady=3, sticky="w")

        # Кнопки
        btns = tk.Frame(ctrl, bg=CSL_WHITE)
        btns.pack(fill=tk.X, pady=8)

        tk.Button(btns, text="💾 Сохранить отчет", bg="#374151", fg="white", bd=0, padx=12, pady=7,
                  command=self.save_report).pack(side=tk.LEFT, padx=(0,5))

        tk.Button(btns, text=f"📧 Отправить на {ADMIN_EMAIL} (SMTP)", bg="#10B981", fg="white", font=("Segoe UI", 10, "bold"),
                  bd=0, padx=14, pady=7, command=lambda: self.threaded(self.send_report_email_smtp)).pack(side=tk.LEFT, padx=5)

        tk.Button(btns, text="📨 Открыть в Outlook / Почте", bg=CSL_ORANGE, fg="white", bd=0, padx=12, pady=7,
                  command=lambda: self.threaded(self.send_report_email_outlook)).pack(side=tk.LEFT, padx=5)

        tk.Button(btns, text="⚙ SMTP", bg="#E5E7EB", fg=CSL_TEXT, bd=0, padx=10, pady=7,
                  command=self.open_smtp_settings).pack(side=tk.LEFT, padx=5)

        tk.Button(btns, text="🌐 csl.by", bg=CSL_WHITE, fg=CSL_ORANGE, bd=1, relief=tk.SOLID, padx=10, pady=7,
                  command=lambda: webbrowser.open("https://csl.by")).pack(side=tk.RIGHT)

        txt = scrolledtext.ScrolledText(parent, font=("Consolas", 9), bg=CSL_WHITE)
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,15))
        txt.config(state=tk.DISABLED)
        self.logs["report"] = txt

    # ============ EMAIL DIALOG ============

    def open_smtp_settings(self):
        cfg = load_email_config()
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройки SMTP - CSL-Tools")
        dialog.geometry("480x420")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=CSL_WHITE)

        tk.Label(dialog, text="Настройки SMTP для отправки на admin@csl.by", font=("Segoe UI", 12, "bold"), bg=CSL_WHITE).pack(pady=12, padx=15, anchor="w")
        tk.Label(dialog, text="Если у вас корпоративная почта, укажите ваш SMTP. Или используйте mail.csl.by", font=("Segoe UI", 9), bg=CSL_WHITE, fg=CSL_TEXT_LIGHT, wraplength=440, justify="left").pack(padx=15, anchor="w")

        form = tk.Frame(dialog, bg=CSL_WHITE)
        form.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        fields = [
            ("SMTP Сервер:", "smtp_server", "mail.csl.by"),
            ("Порт:", "smtp_port", "587"),
            ("Логин (email):", "smtp_user", ""),
            ("Пароль:", "smtp_pass", ""),
            ("От кого (From):", "from_email", ""),
        ]
        entries = {}
        for i, (label, key, placeholder) in enumerate(fields):
            tk.Label(form, text=label, bg=CSL_WHITE, font=("Segoe UI", 9)).grid(row=i, column=0, sticky="e", pady=6, padx=5)
            ent = tk.Entry(form, font=("Segoe UI", 9), width=30, show="*" if "Пароль" in label else "")
            ent.insert(0, str(cfg.get(key, placeholder)))
            ent.grid(row=i, column=1, sticky="ew", pady=6, padx=5)
            entries[key] = ent

        form.grid_columnconfigure(1, weight=1)

        tls_var = tk.BooleanVar(value=cfg.get("use_tls", True))
        tk.Checkbutton(form, text="Использовать STARTTLS (порт 587)", variable=tls_var, bg=CSL_WHITE, font=("Segoe UI", 9)).grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=8)

        def save():
            new_cfg = {
                "smtp_server": entries["smtp_server"].get().strip(),
                "smtp_port": entries["smtp_port"].get().strip() or "587",
                "smtp_user": entries["smtp_user"].get().strip(),
                "smtp_pass": entries["smtp_pass"].get(),
                "from_email": entries["from_email"].get().strip(),
                "use_tls": tls_var.get(),
                "to_email": self.to_email_entry.get().strip() if hasattr(self, 'to_email_entry') else ADMIN_EMAIL,
                "client_name": self.client_name_entry.get().strip() if hasattr(self, 'client_name_entry') else "",
                "client_phone": self.client_phone_entry.get().strip() if hasattr(self, 'client_phone_entry') else "",
            }
            save_email_config(new_cfg)
            self.email_config = new_cfg
            messagebox.showinfo("SMTP", "Настройки сохранены", parent=dialog)
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=CSL_WHITE)
        btn_frame.pack(fill=tk.X, padx=15, pady=10)
        tk.Button(btn_frame, text="💾 Сохранить", bg=CSL_ORANGE, fg="white", bd=0, padx=20, pady=8, command=save).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Отмена", bg="#E5E7EB", bd=0, padx=15, pady=8, command=dialog.destroy).pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="Тест отправки", bg="#374151", fg="white", bd=0, padx=12, pady=8,
                  command=lambda: self.threaded(self.test_smtp, entries, tls_var)).pack(side=tk.RIGHT)

    def test_smtp(self, entries, tls_var):
        cfg = {
            "smtp_server": entries["smtp_server"].get().strip(),
            "smtp_port": entries["smtp_port"].get().strip(),
            "smtp_user": entries["smtp_user"].get().strip(),
            "smtp_pass": entries["smtp_pass"].get(),
            "from_email": entries["from_email"].get().strip(),
            "use_tls": tls_var.get(),
        }
        try:
            self.set_status("Тест SMTP...")
            send_email_smtp(cfg.get("smtp_user") or ADMIN_EMAIL, "CSL-Tools тест", "Тестовое письмо от CSL-Tools", None, cfg)
            messagebox.showinfo("SMTP", f"Тестовое письмо отправлено на {cfg.get('smtp_user')}")
            self.set_status("SMTP тест OK")
        except Exception as e:
            messagebox.showerror("SMTP Ошибка", str(e))
            self.set_status(f"SMTP ошибка: {e}")

    # ============ ACTIONS ============

    def refresh_adapters(self):
        self.set_status("Получение информации о сетевых адаптерах...")
        self.clear_log("adapters")
        info = get_network_adapters_info()
        self.log("adapters", "=== ipconfig /all ===\n" + info.get('ipconfig','')[:8000])
        self.log("adapters", "\n=== Get-NetAdapter ===\n" + info.get('adapters','')[:5000])
        self.log("adapters", "\n=== netsh ===\n" + info.get('netsh','')[:5000])
        if HAS_PSUTIL:
            try:
                addrs = psutil.net_if_addrs()
                stats = psutil.net_if_stats()
                for name, snics in addrs.items():
                    st = stats.get(name)
                    self.log("adapters", f"\n[{name}] {'UP' if st and st.isup else 'DOWN'} Speed={st.speed if st else '?'}")
                    for snic in snics:
                        self.log("adapters", f"  {snic.family.name}: {snic.address} / {snic.netmask}")
            except Exception as e:
                self.log("adapters", f"psutil error: {e}")
        self.set_status("Адаптеры обновлены")
        self.dashboard_cards["adapters"].config(text="OK", fg=CSL_SUCCESS)

    def refresh_vpn(self):
        self.set_status("Проверка VPN и Прокси...")
        self.clear_log("vpn")
        res = check_vpn_proxy()
        self.log("vpn", "=== VPN ===")
        if res["vpn"]:
            for v in res["vpn"]:
                self.log("vpn", f"[!] {v}")
            self.dashboard_cards["vpn"].config(text="Найден VPN!", fg=CSL_WARN)
        else:
            self.log("vpn", "VPN не обнаружен")
            self.dashboard_cards["vpn"].config(text="Чисто", fg=CSL_SUCCESS)
        self.log("vpn", "\n=== PROXY ===")
        if res["proxy"]:
            for p in res["proxy"]:
                self.log("vpn", f"[!] {p}")
            self.dashboard_cards["vpn"].config(text="Прокси!", fg=CSL_WARN)
        else:
            self.log("vpn", "Прокси не обнаружен")
        self.log("vpn", "\n=== Детали ===\n" + res["details"][:8000])
        self.set_status("VPN/Прокси проверены")

    def do_ping(self):
        hosts = [h.strip() for h in self.ping_entry.get().split(",") if h.strip()]
        self.clear_log("ping")
        self.set_status(f"Пинг {hosts}...")
        results = ping_test(hosts)
        ok_count = 0
        for host, data in results.items():
            self.log("ping", f"\n--- PING {host} ---\n{data['output'][:2000]}")
            if data["success"]:
                ok_count += 1
        self.dashboard_cards["ping"].config(text=f"{ok_count}/{len(hosts)} OK", fg=CSL_SUCCESS if ok_count==len(hosts) else CSL_ERROR)
        self.set_status("Пинг завершен")

    def do_traceroute(self):
        hosts = [h.strip() for h in self.ping_entry.get().split(",") if h.strip()][:3]
        self.clear_log("ping")
        self.set_status(f"Трассировка {hosts}...")
        results = traceroute_test(hosts)
        for host, data in results.items():
            self.log("ping", f"\n--- TRACEROUTE {host} ---\n{data['output'][:4000]}")
        self.set_status("Трассировка завершена")

    def refresh_dns(self):
        self.clear_log("dns")
        self.set_status("Проверка DNS/DHCP...")
        res = check_dns_dhcp()
        self.log("dns", "=== DNS Серверы ===")
        for s in res["dns_servers"]:
            self.log("dns", s)
        self.log("dns", f"\nDHCP Enabled: {res['dhcp_enabled']}")
        self.log("dns", "\n=== Разрешение имен ===")
        for h, r in res["resolution"].items():
            self.log("dns", f"{h}: {r}")
        self.log("dns", "\n=== nslookup csl.by ===\n" + res["nslookup"][:2000])
        ok = sum(1 for v in res["resolution"].values() if "OK" in v)
        self.dashboard_cards["dns"].config(text=f"DNS {ok}/4", fg=CSL_SUCCESS if ok>=3 else CSL_ERROR)
        self.set_status("DNS проверен")

    def refresh_internet(self):
        self.clear_log("dns")
        self.set_status("Проверка интернета...")
        res = check_internet()
        self.log("dns", f"=== Интернет: {'Подключен' if res['connected'] else 'НЕТ ПОДКЛЮЧЕНИЯ'} ===\n")
        for name, status in res["tests"].items():
            self.log("dns", f"{name}: {status}")
        self.dashboard_cards["internet"].config(text="OK" if res["connected"] else "НЕТ", fg=CSL_SUCCESS if res["connected"] else CSL_ERROR)
        self.set_status("Интернет проверен")

    def refresh_bsod(self):
        self.clear_log("bsod")
        self.set_status("Анализ BSOD...")
        res = analyze_bluescreen()
        self.log("bsod", f"=== {res['summary']} ===\n")
        self.log("bsod", f"Minidumps найдено: {len(res['minidumps'])}")
        for d in res["minidumps"]:
            self.log("bsod", f"  {d.get('mtime','')} | {d['name']} | {d.get('size','?')} bytes")
        self.log("bsod", f"\nMEMORY.DMP: {'Есть' if res['memory_dump'] else 'Нет'}")
        if res.get("crashcontrol"):
            self.log("bsod", "\n=== CrashControl ===\n" + res["crashcontrol"][:2000])
        self.log("bsod", "\n=== Журнал BugCheck ===\n" + res["bugcheck_events"][:8000])
        self.dashboard_cards["bsod"].config(text=f"{len(res['minidumps'])} дампов" if res['minidumps'] else "Чисто", fg=CSL_ERROR if res['minidumps'] else CSL_SUCCESS)
        self.set_status("BSOD анализ завершен")

    def open_minidump(self):
        path = "C:\\Windows\\Minidump"
        if is_windows() and os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showinfo("Minidump", f"Путь: {path}")

    def fix_dns(self):
        self.clear_log("fix")
        self.log("fix", fix_flush_dns())
        self.set_status("DNS кеш очищен")

    def fix_renew(self):
        self.clear_log("fix")
        self.log("fix", fix_release_renew())
        self.set_status("IP обновлен")

    def fix_reset(self):
        if not is_admin():
            messagebox.showwarning("Права", "Запустите от Администратора!")
            return
        self.clear_log("fix")
        self.log("fix", fix_reset_ip())
        self.set_status("Winsock/IP сброшены")

    def fix_proxy(self):
        self.clear_log("fix")
        self.log("fix", fix_disable_proxy())
        self.set_status("Прокси отключен")

    def fix_dns_auto(self):
        self.clear_log("fix")
        self.log("fix", fix_set_dns_auto())
        self.set_status("DNS установлен")

    def fix_adapter(self):
        if not is_admin():
            messagebox.showwarning("Права", "Запустите от Администратора!")
            return
        self.clear_log("fix")
        self.log("fix", fix_restart_adapter())
        self.set_status("Адаптер перезапущен")

    def fix_full(self):
        if not is_admin():
            messagebox.showwarning("Права", "Запустите от Администратора!")
            return
        if not messagebox.askyesno("Полный сброс", "Выполнить полный сброс сети? Потребуется перезагрузка!"):
            return
        self.clear_log("fix")
        self.log("fix", "=== ПОЛНЫЙ СБРОС СЕТИ ===\n")
        self.log("fix", fix_flush_dns())
        self.log("fix", "\n" + fix_disable_proxy())
        self.log("fix", "\n" + fix_reset_ip())
        self.log("fix", "\n=== Готово. Перезагрузите ПК ===")
        self.set_status("Полный сброс выполнен")

    def run_auto_diagnostics(self):
        self.clear_log("dashboard")
        self.clear_log("report")
        self.log("dashboard", f"=== CSL-Tools v{APP_VERSION} Авто-диагностика {datetime.datetime.now()} ===\n")
        self.log("report", f"CSL-Tools Отчет {datetime.datetime.now()}\n{COMPANY} {SITE}\n{'='*60}\n")

        def add_both(text):
            self.log("dashboard", text)
            self.log("report", text)

        add_both(f"OS: {platform.system()} {platform.release()} {platform.version()}")
        add_both(f"Hostname: {socket.gethostname()}")
        try:
            add_both(f"IP: {socket.gethostbyname(socket.gethostname())}")
        except:
            pass
        add_both(f"Admin: {is_admin()}\n")

        self.set_status("Шаг 1/6: Интернет...")
        internet = check_internet()
        add_both(f"\n[1] ИНТЕРНЕТ: {'ОК' if internet['connected'] else 'НЕТ ДОСТУПА'}")
        for k,v in internet["tests"].items():
            add_both(f"  {k}: {v}")
        self.dashboard_cards["internet"].config(text="OK" if internet["connected"] else "НЕТ", fg=CSL_SUCCESS if internet["connected"] else CSL_ERROR)

        self.set_status("Шаг 2/6: Адаптеры...")
        adapters = get_network_adapters_info()
        add_both(f"\n[2] АДАПТЕРЫ:\n{adapters['ipconfig'][:3000]}")
        self.dashboard_cards["adapters"].config(text="Проверено", fg=CSL_SUCCESS)

        self.set_status("Шаг 3/6: VPN/Proxy...")
        vp = check_vpn_proxy()
        add_both(f"\n[3] VPN: {vp['vpn'] if vp['vpn'] else 'Не найден'}")
        add_both(f"[3] PROXY: {vp['proxy'] if vp['proxy'] else 'Не найден'}")
        self.dashboard_cards["vpn"].config(text="Найден!" if vp["vpn"] or vp["proxy"] else "Чисто", fg=CSL_WARN if vp["vpn"] or vp["proxy"] else CSL_SUCCESS)

        self.set_status("Шаг 4/6: DNS/DHCP...")
        dns = check_dns_dhcp()
        add_both(f"\n[4] DNS: {dns['dns_servers']}")
        for h,r in dns["resolution"].items():
            add_both(f"  {h}: {r}")
        ok_dns = sum(1 for v in dns["resolution"].values() if "OK" in v)
        self.dashboard_cards["dns"].config(text=f"{ok_dns}/4", fg=CSL_SUCCESS if ok_dns>=3 else CSL_ERROR)

        self.set_status("Шаг 5/6: Пинг...")
        pings = ping_test()
        add_both(f"\n[5] ПИНГ:")
        ok_ping = 0
        for h,d in pings.items():
            if d["success"]: ok_ping+=1
            add_both(f"  {h}: {'OK' if d['success'] else 'FAIL'}")
        self.dashboard_cards["ping"].config(text=f"{ok_ping}/{len(pings)}", fg=CSL_SUCCESS if ok_ping>=3 else CSL_ERROR)

        self.set_status("Шаг 6/6: BSOD...")
        bsod = analyze_bluescreen()
        add_both(f"\n[6] BSOD: {bsod['summary']}")
        add_both(f"  Дампов: {len(bsod['minidumps'])}")
        self.dashboard_cards["bsod"].config(text=f"{len(bsod['minidumps'])} дампов" if bsod["minidumps"] else "Чисто", fg=CSL_ERROR if bsod["minidumps"] else CSL_SUCCESS)

        add_both("\n" + "="*60)
        add_both("РЕКОМЕНДАЦИИ:")
        if not internet["connected"]:
            add_both(" - Нет интернета: Release/Renew, Сброс Winsock, Перезапуск адаптера")
        if vp["proxy"]:
            add_both(" - Обнаружен прокси: отключите если не нужен")
        if ok_dns < 3:
            add_both(" - Проблемы DNS: flushdns, 8.8.8.8 / 1.1.1.1")
        if ok_ping < 3:
            add_both(" - Потери пинга: проверьте кабель/Wi-Fi")
        if bsod["minidumps"]:
            add_both(" - BSOD: проверьте драйвера, память")
        if internet["connected"] and ok_dns>=3 and ok_ping>=3:
            add_both(" - Сеть работает нормально")

        add_both(f"\nОтчет подготовлен {COMPANY} | {SITE} | {CONTACTS['phone']} | {ADMIN_EMAIL}")
        self.set_status("Авто-диагностика завершена")

    def get_report_text(self):
        if "report" in self.logs:
            w = self.logs["report"]
            w.config(state=tk.NORMAL)
            content = w.get(1.0, tk.END)
            w.config(state=tk.DISABLED)
            if content.strip():
                return content
        w = self.logs["dashboard"]
        w.config(state=tk.NORMAL)
        content = w.get(1.0, tk.END)
        w.config(state=tk.DISABLED)
        return content

    def save_report(self):
        content = self.get_report_text()
        if not content.strip():
            messagebox.showwarning("Отчет", "Сначала запустите диагностику")
            return None
        default_name = f"CSL-Tools_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "Рабочий стол"
        if not desktop.exists():
            desktop = Path.cwd()
        file_path = desktop / default_name
        try:
            path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=default_name, initialdir=str(desktop),
                                                filetypes=[("Text", "*.txt"), ("All", "*.*")])
            if not path:
                path = str(file_path)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
                f.write(f"\n\n---\n{APP_NAME} v{APP_VERSION} | {COMPANY} | {SITE}\n{CONTACTS['address']} | {CONTACTS['phone']} | {ADMIN_EMAIL}\n")
                f.write(f"Клиент: {self.client_name_entry.get() if hasattr(self,'client_name_entry') else ''} | Тел: {self.client_phone_entry.get() if hasattr(self,'client_phone_entry') else ''}\n")
            messagebox.showinfo("Отчет", f"Отчет сохранен:\n{path}")
            self.set_status(f"Отчет сохранен: {path}")
            self.last_report_path = path
            return path
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
            return None

    def save_report_temp(self):
        content = self.get_report_text()
        if not content.strip():
            return None
        temp_dir = Path.cwd() / "temp_reports"
        temp_dir.mkdir(exist_ok=True)
        cfg = load_email_config()
        client = cfg.get("client_name") or self.client_name_entry.get() if hasattr(self, 'client_name_entry') else "Unknown"
        fname = f"CSL-Report_{socket.gethostname()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = temp_dir / fname
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"Клиент: {client}\n")
                f.write(f"Телефон: {self.client_phone_entry.get() if hasattr(self,'client_phone_entry') else ''}\n")
                f.write(f"ПК: {socket.gethostname()}\n")
                f.write(f"Дата: {datetime.datetime.now()}\n")
                f.write(f"{'='*60}\n\n")
                f.write(content)
            self.last_report_path = str(path)
            return str(path)
        except Exception as e:
            print(f"Temp save error: {e}")
            return None

    # === EMAIL SENDING ===

    def send_report_email_quick(self):
        # Быстрая отправка без диалога - использует сохраненный SMTP или открывает mailto
        cfg = load_email_config()
        # обновляем из полей
        if hasattr(self, 'client_name_entry'):
            cfg["client_name"] = self.client_name_entry.get().strip()
            cfg["client_phone"] = self.client_phone_entry.get().strip()
            cfg["to_email"] = self.to_email_entry.get().strip() or ADMIN_EMAIL
            save_email_config(cfg)
            self.email_config = cfg

        if not cfg.get("smtp_user"):
            # Нет SMTP - открываем диалог
            if messagebox.askyesno("SMTP не настроен", f"SMTP не настроен для отправки на {ADMIN_EMAIL}.\n\nОткрыть настройки SMTP?\n\nИли отправить через Outlook/почтовый клиент?"):
                self.open_smtp_settings()
            else:
                self.send_report_email_outlook()
            return

        self.send_report_email_smtp()

    def send_report_email_smtp(self):
        self.set_status(f"Отправка отчета на {ADMIN_EMAIL} через SMTP...")
        report_path = self.save_report_temp()
        if not report_path:
            messagebox.showwarning("Отчет", "Сначала запустите диагностику!")
            return

        cfg = load_email_config()
        if hasattr(self, 'client_name_entry'):
            cfg["client_name"] = self.client_name_entry.get().strip()
            cfg["client_phone"] = self.client_phone_entry.get().strip()
            cfg["to_email"] = self.to_email_entry.get().strip() or ADMIN_EMAIL
            save_email_config(cfg)

        to_email = cfg.get("to_email", ADMIN_EMAIL) or ADMIN_EMAIL
        client_name = cfg.get("client_name", "") or "Не указан"
        client_phone = cfg.get("client_phone", "") or "Не указан"

        subject = f"[CSL-Tools] Отчет диагностики {socket.gethostname()} {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')} - {client_name}"
        body = f"""Здравствуйте!

Отправлен отчет диагностики сети CSL-Tools v{APP_VERSION}

Клиент: {client_name}
Телефон: {client_phone}
Компьютер: {socket.gethostname()}
Дата: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
OS: {platform.system()} {platform.release()}
IP: {socket.gethostbyname(socket.gethostname()) if True else ''}

Отчет во вложении.

---
{APP_NAME} v{APP_VERSION} | {COMPANY} | {SITE}
{CONTACTS['address']} | {CONTACTS['phone']} | {ADMIN_EMAIL}
10 лет • 160 серверов • 80 клиентов
"""

        try:
            # Проверка SMTP конфига
            if not cfg.get("smtp_server") or not cfg.get("smtp_user"):
                raise ValueError("SMTP не настроен. Укажите сервер и логин в настройках.")

            send_email_smtp(to_email, subject, body, report_path, cfg)
            messagebox.showinfo("Отправка", f"Отчет успешно отправлен на {to_email}\n\nФайл: {Path(report_path).name}")
            self.set_status(f"Отчет отправлен на {to_email}")
            self.log("report", f"\n[EMAIL] Отчет отправлен на {to_email} через SMTP {cfg.get('smtp_server')}:{cfg.get('smtp_port')}")
        except Exception as e:
            err = str(e)
            self.log("report", f"\n[EMAIL ОШИБКА SMTP] {err}")
            self.set_status(f"Ошибка SMTP: {err}")
            # Предложить fallback
            if messagebox.askyesno("Ошибка SMTP", f"Не удалось отправить через SMTP:\n{err}\n\nПопробовать отправить через Outlook / почтовый клиент (mailto)?"):
                self.send_report_email_outlook(report_path)

    def send_report_email_outlook(self, report_path=None):
        if not report_path:
            report_path = self.save_report_temp()
        if not report_path:
            messagebox.showwarning("Отчет", "Сначала запустите диагностику!")
            return

        cfg = load_email_config()
        to_email = self.to_email_entry.get().strip() if hasattr(self, 'to_email_entry') else cfg.get("to_email", ADMIN_EMAIL)
        client_name = self.client_name_entry.get().strip() if hasattr(self, 'client_name_entry') else cfg.get("client_name","")
        client_phone = self.client_phone_entry.get().strip() if hasattr(self, 'client_phone_entry') else cfg.get("client_phone","")

        subject = f"[CSL-Tools] Отчет {socket.gethostname()} - {client_name}"
        body = f"""Здравствуйте, CSL!

Отчет диагностики сети CSL-Tools v{APP_VERSION}
Клиент: {client_name}
Телефон: {client_phone}
ПК: {socket.gethostname()}
Дата: {datetime.datetime.now()}

Вложение: {Path(report_path).name}
Путь к файлу: {report_path}

Пожалуйста, проанализируйте и свяжитесь.

---
{COMPANY} | {SITE} | {ADMIN_EMAIL}
"""

        self.set_status("Открытие почтового клиента...")
        # Попытка PowerShell Outlook
        try:
            ok, out = send_via_powershell(to_email, subject, body, report_path)
            if ok:
                self.log("report", f"\n[EMAIL] Открыт Outlook с письмом на {to_email}, файл {report_path}")
                self.set_status(f"Outlook открыт для отправки на {to_email}")
                messagebox.showinfo("Почта", f"Outlook / почтовый клиент открыт.\n\nКому: {to_email}\nФайл: {Path(report_path).name}\n\nНажмите Отправить в почтовом клиенте.")
                return
        except Exception as e:
            print(f"Outlook fail: {e}")

        # Fallback mailto
        if open_mailto(to_email, subject, body + f"\n\nФайл отчета сохранен: {report_path}\nПрикрепите его вручную."):
            self.log("report", f"\n[EMAIL] Открыт mailto:{to_email}, файл {report_path} нужно прикрепить вручную")
            messagebox.showinfo("Почта", f"Почтовый клиент открыт (mailto).\n\nКому: {to_email}\n\nВАЖНО: Прикрепите файл вручную:\n{report_path}")
            self.set_status(f"mailto открыт для {to_email}")
        else:
            messagebox.showwarning("Почта", f"Не удалось открыть почтовый клиент.\n\nОтчет сохранен: {report_path}\nОтправьте его вручную на {to_email}")
            self.set_status("Не удалось открыть почту")

def main():
    if tk is None:
        print("Tkinter не доступен, консольный режим")
        return
    root = tk.Tk()
    if is_windows():
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    app = CSLToolsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
