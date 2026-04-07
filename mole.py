#!/usr/bin/env python3
"""
mole.py — launcher for the Mole transparent proxy client.

Detects the OS and architecture, selects the correct mole binary from this
directory, and exec's it with client.yaml (plus any extra arguments passed
to this script).

Must run as root / Administrator. If not, automatically re-launches itself
with sudo (Linux / macOS) or UAC elevation (Windows).

Usage:
    python3 mole.py                       # auto-elevates if needed
    python3 mole.py --check               # probe servers, no system changes
    python3 mole.py --config /path/to/other.yaml
"""

import ctypes
import os
import platform
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

BINARY_MAP = {
    ("linux",   "x86_64"):  "mole_linux_amd64",
    ("linux",   "aarch64"): "mole_linux_arm64",
    ("linux",   "armv7l"):  "mole_linux_arm64",
    ("darwin",  "x86_64"):  "mole_darwin_amd64",
    ("darwin",  "arm64"):   "mole_darwin_arm64",
    ("windows", "AMD64"):   "mole_windows_amd64.exe",
    ("windows", "x86_64"):  "mole_windows_amd64.exe",
}

DEFAULT_CONFIG = SCRIPT_DIR / "client.yaml"


def die(msg):
    print(f"[✗] {msg}", file=sys.stderr)
    sys.exit(1)


def ensure_root(os_name):
    """Re-exec with elevated privileges if not already root / Administrator."""
    if os_name == "windows":
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            is_admin = False

        if not is_admin:
            # Re-launch this script with UAC elevation and wait for it to finish.
            args = " ".join(f'"{a}"' for a in sys.argv)
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, args, None, 1
            )
            # ShellExecuteW returns > 32 on success.
            if ret <= 32:
                die("UAC elevation failed or was denied.")
            sys.exit(0)
    else:
        if os.geteuid() != 0:
            # Re-exec this script under sudo, replacing the current process.
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)


def main():
    os_name  = platform.system().lower()
    machine  = platform.machine()

    ensure_root(os_name)

    filename = BINARY_MAP.get((os_name, machine))

    if not filename:
        die(f"Unsupported platform: {os_name}/{machine}\n"
            f"    Supported: {', '.join(f'{o}/{m}' for o, m in BINARY_MAP)}")

    binary = SCRIPT_DIR / filename
    if not binary.exists():
        die(f"Binary not found: {binary}\n"
            f"    Expected alongside mole.py in: {SCRIPT_DIR}")

    # If the caller didn't pass --config, inject the default.
    args = sys.argv[1:]
    if "--config" not in args:
        if not DEFAULT_CONFIG.exists():
            die(f"client.yaml not found: {DEFAULT_CONFIG}\n"
                f"    Pass --config /path/to/client.yaml to specify one.")
        args = ["--config", str(DEFAULT_CONFIG)] + args

    # exec replaces this process with the binary — signals (Ctrl+C) go
    # directly to mole, and its exit code becomes the exit code of this script.
    os.execv(str(binary), [str(binary)] + args)


if __name__ == "__main__":
    main()
