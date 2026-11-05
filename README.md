<details>
<summary><strong>FULL DISCLOSURE</strong> — AI Development & Legal Notice</summary>

---

### AI Development Disclosure

This tool is part of the **pr0t31n toolkit**, a collection of security testing and penetration testing automation tools. The toolkit was created through AI-assisted development, guided by the professional experience and domain expertise of a cybersecurity consultant and penetration tester. Ya, I named it after myself - but to be fair, AI is horrible at naming things.

**The pr0t31n toolkit exists to serve two purposes:**

1. **Automate repetitive penetration testing workflow steps.** Security assessments involve significant amounts of repetitive, procedural work — running sequential tool chains, parsing outputs, correlating findings across tools, and managing engagement data. Automating these steps frees testers to focus on the work that requires human judgment: manual testing, creative attack paths, analysis, and reporting.

2. **Demonstrate the benefits and failures of AI-assisted development.** This toolkit is a real-world case study in building production security tooling with AI assistance. It demonstrates both what AI-assisted development can accomplish and where it falls short. The quality of AI-generated code varies significantly — between context refreshes, the output can range from senior/principal-level software engineering to the work of a still-in-school intern. This inconsistency is itself part of the demonstration.

In the interest of transparency, every tool in the pr0t31n toolkit carries this disclosure. The creator believes that AI-assisted development should be acknowledged openly, not concealed. Users, reviewers, and anyone examining this code should know how it was built so they can evaluate it accordingly.

---

### Legal & Authorization Notice

> **⚠ WARNING: AUTHORIZED USE ONLY**

This tool is designed and intended **exclusively** for use in **authorized security testing engagements**. "Authorized" means **all** of the following conditions are met:

- **Explicit Written Permission.** You possess explicit, documented, written authorization from the owner or authorized representative of the target system(s), network(s), or application(s) to conduct security testing. Verbal agreements are not sufficient.
- **Defined Scope.** The authorization clearly defines the scope of testing, including which systems, networks, IP ranges, applications, and/or endpoints are included. You must not exceed the boundaries of this defined scope under any circumstances.
- **Defined Timeframe.** The authorization specifies the dates and times during which testing is permitted. Testing outside the authorized window is unauthorized testing.
- **Rules of Engagement.** You are operating under a set of rules of engagement (RoE) or equivalent governing document that establishes acceptable testing methods, escalation procedures, emergency contacts, and any restrictions or exclusions.
- **Legal Compliance.** Your testing complies with all applicable local, state, national, and international laws and regulations, including but not limited to the Computer Fraud and Abuse Act (CFAA), the General Data Protection Regulation (GDPR), and equivalent legislation in your jurisdiction.

**Prohibited uses** include but are not limited to: unauthorized access to or testing of any system; testing against systems without explicit written authorization; any activity that violates applicable laws; use for malicious purposes including data theft, extortion, sabotage, or disruption of services; distribution intended to facilitate unauthorized access; and use without a clear legal basis.

**THIS TOOL IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT.**

The creator(s) and contributor(s) accept no responsibility or liability for any damage, loss, legal consequence, or other harm resulting from the use or misuse of this tool — including damage to systems or data, legal penalties or prosecution, loss of data or revenue, and any direct, indirect, incidental, special, consequential, or punitive damages.

**By using this tool, you acknowledge that you are solely responsible for ensuring that your use is authorized, lawful, and within the defined scope of your engagement. You assume all risk associated with the use of this tool.**

Security testing is a professional discipline with significant ethical and legal obligations. Users operating in a professional capacity are expected to adhere to the standards and codes of conduct established by recognized industry bodies, including PTES, OWASP, NIST, and any certifying body under which they hold credentials.

---

</details>

# Mole-Client

Pre-built client for the **Mole** SOCKS5 + DNS transparent proxy suite.

`mole` runs on a device sitting behind a restrictive network. It intercepts all outbound TCP and DNS traffic transparently — applications need no configuration — and tunnels it through a remote `moled` server over SOCKS5. DNS queries bypass network-controlled resolvers entirely.

---


> **[View full documentation on the Codex Wiki](https://wiki.pr0t31n.com/tools/mole-client)** — detailed features, CLI reference, findings catalogue, and integration guides.

## How It Works

```
┌──────────────── RESTRICTED NETWORK ─────────────────────┐
│                                                          │
│  ┌────────────────────────┐                              │
│  │  THIS MACHINE          │      ┌──────────────────┐   │
│  │                        │ VPN  │  MOLE SERVER     │   │
│  │  Any app → TCP :443    │══════│                  │   │
│  │   ↓ iptables REDIRECT  │      │  moled :1080     │   │
│  │  Transparent :1081     │      │   ↓ SOCKS5       │   │
│  │   ↓ SOCKS5 tunnel      │      │  → internet      │   │
│  │                        │      │                  │   │
│  │  Any app → DNS query   │      │  DNS proxy :5353 │   │
│  │   ↓ /etc/resolv.conf   │      │   ↓ 1.1.1.1      │   │
│  │  DNS proxy :53         │      └──────────────────┘   │
│  │   ↓ SOCKS5 tunnel      │                              │
│  └────────────────────────┘                              │
│  Network DNS: COMPLETELY BYPASSED                        │
└──────────────────────────────────────────────────────────┘
```

### Linux (full transparent)
1. iptables `REDIRECT` rules in a dedicated `MOLE_OUTPUT` chain intercept all outbound TCP and send it to a local transparent proxy.
2. `/etc/resolv.conf` is replaced with `nameserver 127.0.0.1` — all DNS goes through the local DNS proxy.
3. Both the TCP proxy and DNS proxy forward traffic through SOCKS5 to the server.
4. `systemd-resolved` is stopped while mole runs (restored on exit).
5. On exit (SIGINT/SIGTERM or service stop), all iptables rules are removed and DNS is restored.

### macOS
`networksetup` is used to set a system-wide SOCKS5 proxy and override DNS to `127.0.0.1` on all active network interfaces. Applications that respect macOS system proxy settings are covered. On exit, all settings are reverted.

### Windows
The WinInet SOCKS5 proxy is set via registry (`HKCU\...\Internet Settings`) and WinHTTP is configured via `netsh`. DNS is overridden on all active adapters via `netsh interface ipv4 set dns`. All settings are reverted on exit.

---

## Contents

| File | Description |
|------|-------------|
| `mole_linux_amd64` | Client binary — Linux x86_64 |
| `mole_linux_arm64` | Client binary — Linux aarch64 / armv7l |
| `mole_darwin_amd64` | Client binary — macOS Intel |
| `mole_darwin_arm64` | Client binary — macOS Apple Silicon |
| `mole_windows_amd64.exe` | Client binary — Windows x86_64 |
| `client.yaml` | Configuration template |
| `Mole-Client-Install.py` | Installer — detects OS/arch, deploys binary and service |

---

## Requirements

| Platform | Requirement |
|----------|-------------|
| Linux | systemd, `iptables`, root |
| macOS | `networksetup` (pre-installed), root |
| Windows | Administrator, Task Scheduler |
| All | VPN connected so the server IP in `client.yaml` is reachable |

---

## Quick Start

### 1. Edit the configuration

```bash
nano client.yaml
```

At minimum, set the server host to the VPN IP of your `moled` server:

```yaml
servers:
  - name: "Primary"
    host: "10.8.0.1"      # VPN IP of your moled server
    socks5_port: 1080
    dns_port: 5353
```

See [Configuration Reference](#configuration-reference) for all options.

### 2. Run the installer

**Linux / macOS:**
```bash
sudo python3 Mole-Client-Install.py
```

**Windows** (Administrator Command Prompt):
```cmd
python3 Mole-Client-Install.py
```

The installer:
- Detects the OS and architecture, selects the correct binary
- Installs the binary to the system binary path
- Deploys `client.yaml` to the system config path
- Creates and enables a persistent service that starts on boot
- Starts the service immediately (unless `--no-start` is passed)

### 3. Verify

**Linux:**
```bash
sudo systemctl status proxysuite-client
sudo journalctl -u proxysuite-client -f
```

**macOS:**
```bash
sudo launchctl list com.proxysuite.mole-client
tail -f /var/log/proxysuite/mole-client.log
```

**Windows:**
```cmd
schtasks /Query /TN MoleClient /FO LIST /V
```

### 4. Confirm traffic is tunnelled

```bash
curl https://ifconfig.me
```

The returned IP should be the server's public IP, not your own.

---

## Configuration Reference

Config is deployed to:
- **Linux / macOS:** `/etc/proxysuite/client-config.yaml`
- **Windows:** `C:\ProgramData\Mole\client-config.yaml`

```yaml
# ── Servers ───────────────────────────────────────────────────────────────────
# Tried in order. The first to respond to a SOCKS5 probe is used.
servers:
  - name: "Primary"
    host: "10.8.0.1"          # VPN IP of the moled server
    socks5_port: 1080          # must match server-config.yaml socks5_port
    dns_port: 5353             # must match server-config.yaml dns_port

  # - name: "Backup"
  #   host: "10.8.0.2"
  #   socks5_port: 1080
  #   dns_port: 5353

# ── Authentication ────────────────────────────────────────────────────────────
# Leave empty unless the server has auth.enabled: true.
# Must match server-config.yaml auth section exactly.
auth:
  username: ""
  password: ""

# ── Local ports ───────────────────────────────────────────────────────────────
local:
  dns_port: 53       # Local DNS proxy — port 53 requires root (Linux) / Admin (Windows)
  socks5_port: 1081  # Local transparent proxy (Linux iptables target) or
                     # system SOCKS5 port (macOS / Windows)

# ── Network / routing ─────────────────────────────────────────────────────────
network:
  # CIDRs that bypass the proxy and go direct.
  # RFC-1918 and loopback are always bypassed regardless of this list.
  bypass_networks:
    - "10.0.0.0/8"
    - "172.16.0.0/12"
    - "192.168.0.0/16"
    # - "100.64.0.0/10"   # Uncomment for Tailscale / CGNAT

  connect_timeout_sec: 10    # seconds before a server probe is declared failed
  retry_attempts: 3          # retries per server before moving to the next
  retry_delay_sec: 2         # seconds between retries

# ── DNS ───────────────────────────────────────────────────────────────────────
dns:
  # Upstream resolver the SERVER contacts on your behalf.
  # All DNS leaves through the SOCKS5 tunnel — the local network never sees it.
  upstream_dns: "8.8.8.8:53"

# ── Logging ───────────────────────────────────────────────────────────────────
logging:
  verbose: true    # false → only errors to stdout; all events still go to log files
```

---

## Service Management

### Linux (systemd)

```bash
# Status
sudo systemctl status proxysuite-client

# Live logs (journald)
sudo journalctl -u proxysuite-client -f

# Start / stop / restart
sudo systemctl start   proxysuite-client
sudo systemctl stop    proxysuite-client   # cleanly reverts iptables + DNS
sudo systemctl restart proxysuite-client

# Enable / disable on boot
sudo systemctl enable  proxysuite-client
sudo systemctl disable proxysuite-client
```

### macOS (launchd)

```bash
# Status
sudo launchctl list com.proxysuite.mole-client

# Live log
tail -f /var/log/proxysuite/mole-client.log

# Restart
sudo launchctl kickstart -k system/com.proxysuite.mole-client

# Stop (reverts proxy and DNS settings)
sudo launchctl unload /Library/LaunchDaemons/com.proxysuite.mole-client.plist

# Re-enable
sudo launchctl load -w /Library/LaunchDaemons/com.proxysuite.mole-client.plist
```

### Windows (Task Scheduler)

```cmd
:: Status
schtasks /Query /TN MoleClient /FO LIST /V

:: Start
schtasks /Run /TN MoleClient

:: Stop (reverts proxy and DNS settings)
schtasks /End /TN MoleClient

:: Open Task Scheduler GUI
taskschd.msc
```

---

## Installer Options

```
sudo python3 Mole-Client-Install.py [OPTIONS]

  --config FILE    Path to client.yaml to deploy
                   (default: ./client.yaml alongside the installer)
  --no-start       Register the service but do not start it yet
  --check          Report installation status without making changes
  --uninstall      Stop/remove the service and binary; preserves config
```

### Check mode

```bash
sudo python3 Mole-Client-Install.py --check
```

Reports platform compatibility, local binary presence, installed binary, config, service registration, and whether the service is active — without making any changes.

### Uninstall

```bash
sudo python3 Mole-Client-Install.py --uninstall
```

Stops and removes the service and binary. Config is preserved. To remove config entirely:

**Linux / macOS:**
```bash
sudo rm -rf /etc/proxysuite
```

**Windows:**
```cmd
rmdir /s /q "C:\ProgramData\Mole"
```

---

## Manual Cleanup After a Crash (Linux)

If mole exits uncleanly and iptables rules or DNS are left behind:

```bash
# Remove iptables rules
sudo iptables -t nat -D OUTPUT -j MOLE_OUTPUT 2>/dev/null
sudo iptables -t nat -F MOLE_OUTPUT 2>/dev/null
sudo iptables -t nat -X MOLE_OUTPUT 2>/dev/null

# Restore DNS
sudo cp /etc/resolv.conf.mole.bak /etc/resolv.conf
sudo systemctl start systemd-resolved
```

---

## Troubleshooting

**All servers unreachable at startup**
```bash
# Probe servers manually (no system changes made)
sudo mole --config /etc/proxysuite/client-config.yaml --check

# Basic reachability
ping 10.8.0.1
nc -zv 10.8.0.1 1080
```
The VPN must be connected before `mole` starts.

**DNS not working after connect (Linux)**
```bash
cat /etc/resolv.conf          # should read: nameserver 127.0.0.1
dig @127.0.0.1 google.com     # test local DNS proxy directly
ss -tulpn | grep :53          # confirm mole is listening
```

**Port 53 already in use (Ubuntu)**

`mole` automatically stops `systemd-resolved` before binding port 53. If it fails:
```bash
sudo systemctl stop systemd-resolved
sudo systemctl restart proxysuite-client
```

**macOS apps not tunnelled**

macOS SOCKS5 system proxy covers most applications, but apps that bypass `SCDynamicStore` (some CLIs, certain VPN clients) will go direct. Check with:
```bash
curl --proxy socks5://127.0.0.1:1081 https://ifconfig.me
```

**Windows apps not tunnelled**

WinInet/WinHTTP coverage applies to most browsers and system services. Terminal apps (curl, PowerShell `Invoke-WebRequest`) vary — some require explicit proxy configuration.

---

## Attribution

`mole` is built on the following open-source libraries.

| Library | Author | Link |
|---------|--------|------|
| `github.com/miekg/dns` | Miek Gieben | https://github.com/miekg/dns |
| `golang.org/x/net/proxy` | The Go Authors / Google | https://pkg.go.dev/golang.org/x/net/proxy |
| `golang.org/x/sys` | The Go Authors / Google | https://pkg.go.dev/golang.org/x/sys |
| `gopkg.in/yaml.v3` | Canonical Ltd / go-yaml team | https://github.com/go-yaml/yaml |

**System tools used at runtime:**

| Tool | Platform | Purpose |
|------|----------|---------|
| iptables (netfilter) | Linux | NAT REDIRECT rules — intercepts outbound TCP |
| networksetup | macOS | System-wide SOCKS5 proxy + DNS override |
| netsh / reg | Windows | WinHTTP proxy + DNS adapter override |
