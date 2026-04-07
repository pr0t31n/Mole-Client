#!/usr/bin/env python3
"""
Mole-Client — Proxysuite transparent SOCKS5 + DNS proxy client (mole)
Install script for /Users/pr0t31n/Mole-Client/

Detects the OS and architecture, installs the correct mole binary, deploys
client.yaml, and creates a persistent service:
  Linux   — systemd unit  (proxysuite-client)
  macOS   — LaunchDaemon  (com.proxysuite.mole-client)
  Windows — Task Scheduler (MoleClient)

Usage:
    Linux / macOS:  sudo python3 Mole-Client-Install.py
    Windows:        python3 Mole-Client-Install.py   (from Admin prompt)

    sudo python3 Mole-Client-Install.py --check
    sudo python3 Mole-Client-Install.py --config /path/to/client.yaml
    sudo python3 Mole-Client-Install.py --no-start
    sudo python3 Mole-Client-Install.py --uninstall
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ─── ANSI colours ─────────────────────────────────────────────────────────────
R = "\033[1;31m"
G = "\033[1;32m"
Y = "\033[1;33m"
B = "\033[1;34m"
C = "\033[1;36m"
W = "\033[0m"
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent

# Binary filenames available in SCRIPT_DIR
BINARY_MAP = {
    ("linux",   "x86_64"):  "mole_linux_amd64",
    ("linux",   "aarch64"): "mole_linux_arm64",
    ("linux",   "armv7l"):  "mole_linux_arm64",
    ("darwin",  "x86_64"):  "mole_darwin_amd64",
    ("darwin",  "arm64"):   "mole_darwin_arm64",
    ("windows", "AMD64"):   "mole_windows_amd64.exe",
    ("windows", "x86_64"):  "mole_windows_amd64.exe",
}

# ── Per-platform install paths ────────────────────────────────────────────────

def _is_windows():
    return platform.system().lower() == "windows"

def _is_darwin():
    return platform.system().lower() == "darwin"

if _is_windows():
    BINARY_DEST   = Path(r"C:\Program Files\Mole\mole.exe")
    CONFIG_DIR    = Path(r"C:\ProgramData\Mole")
    CONFIG_DEST   = CONFIG_DIR / "client-config.yaml"
    LOG_NOTE      = r"C:\ProgramData\Mole\logs\ (created by mole at runtime)"
    TASK_NAME     = "MoleClient"
elif _is_darwin():
    BINARY_DEST   = Path("/usr/local/bin/mole")
    CONFIG_DIR    = Path("/etc/proxysuite")
    CONFIG_DEST   = CONFIG_DIR / "client-config.yaml"
    LOG_DIR       = Path("/var/log/proxysuite")
    PLIST_LABEL   = "com.proxysuite.mole-client"
    PLIST_PATH    = Path(f"/Library/LaunchDaemons/{PLIST_LABEL}.plist")
else:  # linux (default)
    BINARY_DEST   = Path("/usr/local/bin/mole")
    CONFIG_DIR    = Path("/etc/proxysuite")
    CONFIG_DEST   = CONFIG_DIR / "client-config.yaml"
    LOG_NOTE      = "~/.mole/logs/ (written by mole at runtime)"
    SERVICE_NAME  = "proxysuite-client"
    SYSTEMD_UNIT  = Path(f"/etc/systemd/system/{SERVICE_NAME}.service")


# ─── helpers ──────────────────────────────────────────────────────────────────

def banner():
    print(f"""
{C}╔══════════════════════════════════════════════════════╗
║   Mole-Client — Proxysuite Transparent Proxy         ║
║   Install Script                                     ║
╚══════════════════════════════════════════════════════╝{W}
""")


def info(msg):  print(f"{G}[+]{W} {msg}")
def warn(msg):  print(f"{Y}[!]{W} {msg}")
def err(msg):   print(f"{R}[✗]{W} {msg}")
def step(msg):  print(f"\n{B}━━ {msg} ━━{W}")


def run(cmd, **kwargs):
    """Run a command; raise on non-zero exit."""
    print(f"    {C}>{W} {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(str(c) for c in cmd)}")
    return result


def run_ok(cmd, **kwargs):
    """Run a command; return True on success, False on failure."""
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       **kwargs)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def is_admin():
    """Return True if the process has root / Administrator privileges."""
    if _is_windows():
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return os.geteuid() == 0


# ─── OS / arch detection ──────────────────────────────────────────────────────

def detect_platform():
    return platform.system().lower(), platform.machine()


def resolve_binary():
    """Return (Path, filename) for the correct local binary, or exit."""
    os_name, machine = detect_platform()
    key = (os_name, machine)
    filename = BINARY_MAP.get(key)

    if not filename:
        err(f"Unsupported platform: {os_name}/{machine}")
        print(f"  Supported targets:")
        for (o, m), f in BINARY_MAP.items():
            print(f"    {o}/{m}  →  {f}")
        sys.exit(1)

    binary = SCRIPT_DIR / filename
    if not binary.exists():
        err(f"Binary not found: {binary}")
        print(f"  Expected alongside this installer in: {SCRIPT_DIR}")
        sys.exit(1)

    return binary, filename


# ─── Common phases ────────────────────────────────────────────────────────────

def phase_binary(binary_path):
    step("Installing mole Binary")
    BINARY_DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(binary_path), str(BINARY_DEST))
    if not _is_windows():
        BINARY_DEST.chmod(0o755)
    info(f"Installed: {binary_path.name}  →  {BINARY_DEST}")


def phase_config(config_source):
    step("Deploying Configuration")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_DEST.exists():
        backup = CONFIG_DEST.with_suffix(".yaml.bak")
        shutil.copy2(str(CONFIG_DEST), str(backup))
        warn(f"Existing config backed up to {backup}")
    shutil.copy2(str(config_source), str(CONFIG_DEST))
    if not _is_windows():
        CONFIG_DEST.chmod(0o640)
    info(f"Config installed: {CONFIG_DEST}")
    info(f"Edit before starting:  {'notepad' if _is_windows() else 'sudo nano'} {CONFIG_DEST}")


# ─── Linux: systemd ───────────────────────────────────────────────────────────

def phase_service_linux():
    step("Installing systemd Service")

    # mole modifies iptables and /etc/resolv.conf — must run as root.
    unit_content = f"""\
[Unit]
Description=Proxysuite Transparent SOCKS5 + DNS Client (mole)
Documentation=https://github.com/mole
After=network-online.target
Wants=network-online.target

[Service]
Type=simple

# mole requires root to configure iptables and /etc/resolv.conf.
User=root
Group=root

ExecStart={BINARY_DEST} --config {CONFIG_DEST}
Restart=on-failure
RestartSec=10s

# Log to journald (view with: journalctl -u {SERVICE_NAME} -f)
StandardOutput=journal
StandardError=journal
SyslogIdentifier={SERVICE_NAME}

# Give mole time to cleanly revert iptables and DNS on stop.
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
"""
    SYSTEMD_UNIT.write_text(unit_content)
    SYSTEMD_UNIT.chmod(0o644)
    info(f"Unit file written: {SYSTEMD_UNIT}")

    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", SERVICE_NAME])
    info(f"Service enabled (starts on boot)")


def phase_start_linux():
    step("Starting Service")
    if run_ok(["systemctl", "is-active", "--quiet", SERVICE_NAME]):
        info("Service already running — restarting.")
        run(["systemctl", "restart", SERVICE_NAME])
    else:
        run(["systemctl", "start", SERVICE_NAME])
    info(f"Service started: {SERVICE_NAME}")
    info(f"Live logs:  journalctl -u {SERVICE_NAME} -f")


def uninstall_linux():
    step("Uninstalling Mole-Client (Linux)")

    if run_ok(["systemctl", "is-active", "--quiet", SERVICE_NAME]):
        run(["systemctl", "stop", SERVICE_NAME])
        info("Service stopped.")

    if run_ok(["systemctl", "is-enabled", "--quiet", SERVICE_NAME]):
        run(["systemctl", "disable", SERVICE_NAME])
        info("Service disabled.")

    if SYSTEMD_UNIT.exists():
        SYSTEMD_UNIT.unlink()
        run(["systemctl", "daemon-reload"])
        info(f"Unit file removed: {SYSTEMD_UNIT}")

    if BINARY_DEST.exists():
        BINARY_DEST.unlink()
        info(f"Binary removed: {BINARY_DEST}")

    warn(f"Config preserved: {CONFIG_DEST}")
    print(f"\n  To fully remove config:\n    sudo rm -rf {CONFIG_DIR}\n")


def check_linux():
    results = []

    ok = BINARY_DEST.exists() and os.access(str(BINARY_DEST), os.X_OK)
    results.append(("installed binary", ok, str(BINARY_DEST) if ok else "missing"))

    ok = CONFIG_DEST.exists()
    results.append(("config", ok, str(CONFIG_DEST) if ok else "missing"))

    ok = SYSTEMD_UNIT.exists()
    results.append(("systemd unit", ok, str(SYSTEMD_UNIT) if ok else "missing"))

    ok = run_ok(["systemctl", "is-enabled", "--quiet", SERVICE_NAME])
    results.append(("service enabled", ok, "yes" if ok else "no"))

    ok = run_ok(["systemctl", "is-active", "--quiet", SERVICE_NAME])
    results.append(("service active", ok, "running" if ok else "stopped"))

    return results


# ─── macOS: launchd ───────────────────────────────────────────────────────────

def phase_logdir_darwin():
    step("Creating Log Directory")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    info(f"Log directory: {LOG_DIR}")


def phase_service_darwin():
    step("Installing LaunchDaemon")

    plist_content = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>{BINARY_DEST}</string>
        <string>--config</string>
        <string>{CONFIG_DEST}</string>
    </array>

    <!-- Start automatically at boot and keep alive on exit/crash -->
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>

    <!-- Wait for network before starting -->
    <key>NetworkState</key>
    <true/>

    <!-- Stdout/stderr captured to file-based logs -->
    <key>StandardOutPath</key>
    <string>{LOG_DIR}/mole-client.log</string>
    <key>StandardErrorPath</key>
    <string>{LOG_DIR}/mole-client.err.log</string>

    <!-- Throttle restart attempts on repeated failure -->
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
"""
    PLIST_PATH.write_text(plist_content)
    PLIST_PATH.chmod(0o644)
    info(f"LaunchDaemon plist written: {PLIST_PATH}")


def phase_start_darwin():
    step("Loading LaunchDaemon")

    # Unload first if already loaded (handles reinstall / update).
    run_ok(["launchctl", "unload", str(PLIST_PATH)])

    run(["launchctl", "load", "-w", str(PLIST_PATH)])
    info(f"LaunchDaemon loaded: {PLIST_LABEL}")
    info(f"Stdout log:  {LOG_DIR}/mole-client.log")
    info(f"Stderr log:  {LOG_DIR}/mole-client.err.log")


def uninstall_darwin():
    step("Uninstalling Mole-Client (macOS)")

    if PLIST_PATH.exists():
        run_ok(["launchctl", "unload", "-w", str(PLIST_PATH)])
        info("LaunchDaemon unloaded.")
        PLIST_PATH.unlink()
        info(f"Plist removed: {PLIST_PATH}")

    if BINARY_DEST.exists():
        BINARY_DEST.unlink()
        info(f"Binary removed: {BINARY_DEST}")

    warn(f"Config preserved: {CONFIG_DEST}")
    warn(f"Logs preserved:   {LOG_DIR}")
    print(f"\n  To fully remove:\n    sudo rm -rf {CONFIG_DIR} {LOG_DIR}\n")


def check_darwin():
    results = []

    ok = BINARY_DEST.exists() and os.access(str(BINARY_DEST), os.X_OK)
    results.append(("installed binary", ok, str(BINARY_DEST) if ok else "missing"))

    ok = CONFIG_DEST.exists()
    results.append(("config", ok, str(CONFIG_DEST) if ok else "missing"))

    ok = PLIST_PATH.exists()
    results.append(("launchdaemon plist", ok, str(PLIST_PATH) if ok else "missing"))

    # launchctl list returns 0 if the label is loaded
    ok = run_ok(["launchctl", "list", PLIST_LABEL])
    results.append(("launchdaemon loaded", ok, "yes" if ok else "no"))

    return results


# ─── Windows: Task Scheduler ──────────────────────────────────────────────────

def phase_service_windows():
    step("Creating Scheduled Task")

    # Build the command string with proper quoting for schtasks.
    exe  = str(BINARY_DEST)
    cfg  = str(CONFIG_DEST)
    task_cmd = f'"{exe}" --config "{cfg}"'

    # /SC ONSTART — trigger at system startup.
    # /DELAY 0000:30 — wait 30 s for network stack to be ready.
    # /RU SYSTEM — run as the built-in SYSTEM account (equivalent to root).
    # /RL HIGHEST — highest privilege level.
    # /F — force overwrite if the task already exists.
    run([
        "schtasks", "/Create",
        "/TN", TASK_NAME,
        "/TR", task_cmd,
        "/SC", "ONSTART",
        "/DELAY", "0000:30",
        "/RU", "SYSTEM",
        "/RL", "HIGHEST",
        "/F",
    ])
    info(f"Scheduled task created: {TASK_NAME}")
    info( "Trigger: system startup (30-second delay for network readiness)")


def phase_start_windows():
    step("Starting Scheduled Task")
    run(["schtasks", "/Run", "/TN", TASK_NAME])
    info(f"Task started: {TASK_NAME}")
    info(f"View in Task Scheduler: taskschd.msc")
    info(f"Check status:  schtasks /Query /TN {TASK_NAME} /FO LIST /V")


def uninstall_windows():
    step("Uninstalling Mole-Client (Windows)")

    # Stop the running instance first (best-effort).
    run_ok(["schtasks", "/End", "/TN", TASK_NAME])

    if run_ok(["schtasks", "/Query", "/TN", TASK_NAME]):
        run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])
        info(f"Scheduled task deleted: {TASK_NAME}")

    if BINARY_DEST.exists():
        BINARY_DEST.unlink()
        info(f"Binary removed: {BINARY_DEST}")

    warn(f"Config preserved: {CONFIG_DEST}")
    print(f"\n  To fully remove config:\n    rmdir /s /q \"{CONFIG_DIR}\"\n")


def check_windows():
    results = []

    ok = BINARY_DEST.exists()
    results.append(("installed binary", ok, str(BINARY_DEST) if ok else "missing"))

    ok = CONFIG_DEST.exists()
    results.append(("config", ok, str(CONFIG_DEST) if ok else "missing"))

    ok = run_ok(["schtasks", "/Query", "/TN", TASK_NAME])
    results.append(("scheduled task", ok, TASK_NAME if ok else "not found"))

    # Check if the task is currently running
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"],
        capture_output=True, text=True,
    )
    running = "Running" in result.stdout
    results.append(("task running", running, "yes" if running else "no"))

    return results


# ─── check mode ───────────────────────────────────────────────────────────────

def run_check():
    step("Check Mode — Installation Status")

    os_name, machine = detect_platform()
    results = []

    # Platform support
    supported = (os_name, machine) in BINARY_MAP
    results.append(("platform", supported,
                    f"{os_name}/{machine}" if supported else f"{os_name}/{machine} (unsupported)"))

    # Local binary
    filename = BINARY_MAP.get((os_name, machine), "")
    local_bin = SCRIPT_DIR / filename if filename else None
    ok = bool(local_bin and local_bin.exists())
    results.append(("local binary", ok,
                    str(local_bin) if ok else f"{filename} not found in {SCRIPT_DIR}"))

    # Platform-specific checks
    if os_name == "linux":
        results.extend(check_linux())
    elif os_name == "darwin":
        results.extend(check_darwin())
    elif os_name == "windows":
        results.extend(check_windows())

    pad = max(len(r[0]) for r in results) + 2
    print()
    for label, ok_flag, detail in results:
        status = f"{G}OK{W}" if ok_flag else f"{R}FAIL{W}"
        print(f"  {label:<{pad}} {status}  {detail}")

    failed = [r for r in results if not r[1]]
    print()
    if not failed:
        info("All checks passed. mole is installed and active.")
    else:
        warn(f"{len(failed)} item(s) not satisfied — run without --check to install.")
    return len(failed) == 0


# ─── post-install summary ─────────────────────────────────────────────────────

def post_install_summary():
    step("Post-Install Verification Summary")

    os_name, _ = detect_platform()
    results = []

    ok = BINARY_DEST.exists()
    results.append(("binary", ok, str(BINARY_DEST) if ok else "missing"))

    ok = CONFIG_DEST.exists()
    results.append(("config", ok, str(CONFIG_DEST) if ok else "missing"))

    if os_name == "linux":
        ok = SYSTEMD_UNIT.exists()
        results.append(("systemd unit", ok, str(SYSTEMD_UNIT) if ok else "missing"))
        ok = run_ok(["systemctl", "is-enabled", "--quiet", SERVICE_NAME])
        results.append(("service enabled", ok, "yes" if ok else "no"))
        ok = run_ok(["systemctl", "is-active", "--quiet", SERVICE_NAME])
        results.append(("service active", ok, "running" if ok else "not running"))
    elif os_name == "darwin":
        ok = PLIST_PATH.exists()
        results.append(("launchdaemon plist", ok, str(PLIST_PATH) if ok else "missing"))
        ok = run_ok(["launchctl", "list", PLIST_LABEL])
        results.append(("launchdaemon loaded", ok, "yes" if ok else "no"))
    elif os_name == "windows":
        ok = run_ok(["schtasks", "/Query", "/TN", TASK_NAME])
        results.append(("scheduled task", ok, TASK_NAME if ok else "not found"))

    pad = max(len(r[0]) for r in results) + 2
    print()
    for label, ok_flag, detail in results:
        status = f"{G}OK{W}" if ok_flag else f"{R}FAIL{W}"
        print(f"  {label:<{pad}} {status}  {detail}")

    failed = [r for r in results if not r[1]]
    print()
    if not failed:
        info(f"{G}Mole-Client installation complete.{W}")
        _print_next_steps(os_name)
    else:
        warn(f"{len(failed)} item(s) need attention (see above).")


def _print_next_steps(os_name):
    if os_name == "linux":
        print(f"""
  {C}Next steps:{W}
    1. Edit config if needed:   sudo nano {CONFIG_DEST}
    2. Restart after edits:     sudo systemctl restart {SERVICE_NAME}
    3. Live logs:               sudo journalctl -u {SERVICE_NAME} -f
    4. Stop (restores DNS/iptables):  sudo systemctl stop {SERVICE_NAME}
""")
    elif os_name == "darwin":
        print(f"""
  {C}Next steps:{W}
    1. Edit config if needed:   sudo nano {CONFIG_DEST}
    2. Restart after edits:     sudo launchctl kickstart -k system/{PLIST_LABEL}
    3. Stdout log:              tail -f {LOG_DIR}/mole-client.log
    4. Stop (restores proxy/DNS):     sudo launchctl unload {PLIST_PATH}
""")
    elif os_name == "windows":
        print(f"""
  Next steps:
    1. Edit config if needed:   notepad "{CONFIG_DEST}"
    2. Restart task:            schtasks /End /TN {TASK_NAME} && schtasks /Run /TN {TASK_NAME}
    3. View task:               taskschd.msc
    4. Stop:                    schtasks /End /TN {TASK_NAME}
""")


# ─── argument parsing ─────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Installer for Mole-Client (proxysuite transparent proxy daemon)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  sudo python3 {Path(__file__).name}
  sudo python3 {Path(__file__).name} --config /path/to/client.yaml
  sudo python3 {Path(__file__).name} --check
  sudo python3 {Path(__file__).name} --no-start
  sudo python3 {Path(__file__).name} --uninstall
""",
    )
    p.add_argument(
        "--config",
        metavar="FILE",
        default=str(SCRIPT_DIR / "client.yaml"),
        help=f"Path to client.yaml to deploy (default: {SCRIPT_DIR / 'client.yaml'})",
    )
    p.add_argument(
        "--no-start",
        action="store_true",
        help="Install and register the service but do not start it now",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Report installation status without making changes",
    )
    p.add_argument(
        "--uninstall",
        action="store_true",
        help="Stop and remove the service and binary (preserves config)",
    )
    return p.parse_args()


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    banner()
    args = parse_args()
    os_name, machine = detect_platform()

    if args.check:
        ok = run_check()
        sys.exit(0 if ok else 1)

    if args.uninstall:
        if not is_admin():
            err("Must be run as root / Administrator.")
            sys.exit(1)
        if os_name == "linux":
            uninstall_linux()
        elif os_name == "darwin":
            uninstall_darwin()
        elif os_name == "windows":
            uninstall_windows()
        else:
            err(f"Unsupported OS for uninstall: {os_name}")
            sys.exit(1)
        sys.exit(0)

    # ── root / admin check ────────────────────────────────────────────────────
    if not is_admin():
        err("Must be run as root / Administrator.")
        if os_name in ("linux", "darwin"):
            print(f"  Run: sudo python3 {Path(__file__).name}")
        else:
            print(f"  Open an Administrator Command Prompt and re-run.")
        sys.exit(1)

    info(f"Platform: {os_name} / {machine}")

    if os_name not in ("linux", "darwin", "windows"):
        err(f"Unsupported OS: {os_name}")
        sys.exit(1)

    # ── resolve binary ────────────────────────────────────────────────────────
    binary_path, binary_filename = resolve_binary()
    info(f"Selected binary: {binary_filename}")

    # ── config source ─────────────────────────────────────────────────────────
    config_source = Path(args.config)
    if not config_source.exists():
        err(f"Config file not found: {config_source}")
        sys.exit(1)
    info(f"Config source: {config_source}")

    # ── common phases ─────────────────────────────────────────────────────────
    phase_binary(binary_path)
    phase_config(config_source)

    # ── platform service setup ────────────────────────────────────────────────
    if os_name == "linux":
        phase_service_linux()
        if not args.no_start:
            phase_start_linux()

    elif os_name == "darwin":
        phase_logdir_darwin()
        phase_service_darwin()
        if not args.no_start:
            phase_start_darwin()

    elif os_name == "windows":
        phase_service_windows()
        if not args.no_start:
            phase_start_windows()

    post_install_summary()


if __name__ == "__main__":
    main()
