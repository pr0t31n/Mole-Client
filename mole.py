#!/usr/bin/env python3
"""
mole.py — launcher for the Mole transparent proxy client.

Detects the OS and architecture, selects the correct mole binary from this
directory, and exec's it with client.yaml (plus any extra arguments passed
to this script).

Usage:
    sudo python3 mole.py                  # activate proxy
    sudo python3 mole.py --check          # probe servers, no system changes
    sudo python3 mole.py --config /path/to/other.yaml
"""

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


def main():
    os_name  = platform.system().lower()
    machine  = platform.machine()
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
