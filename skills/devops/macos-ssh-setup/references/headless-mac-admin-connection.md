# Headless Mac Admin Connection

**Updated: 2026-06-01 (post-tmux removal)**

## Machine
- Model: MacBook Pro 16" 2021 (MacBookPro18,1)
- Chip: Apple M1 Pro (10-core: 8p + 2e)
- RAM: 32 GB
- macOS: 26.5 (Sequoia)

## Connection Details
- **Username:** `admin`
- **Password:** `0000`
- **SSH key (display → headless, NO passphrase):** `~/.ssh/id_ed25519_headless`
- **SSH host config (`~/.ssh/config`):**

```
Host admin-remote
  HostName 192.168.103.70
  User admin
  IdentityFile ~/.ssh/id_ed25519_headless
  PreferredAuthentications publickey
  StrictHostKeyChecking no
  ServerAliveInterval 5

- **Thunderbolt Bridge IP:** `192.168.2.2` (bridge0, ~0.7ms latency) — most reliable
- **WiFi IP (ship network, static):** `192.168.103.70`
- **ZTE LAN IP (DHCP):** `192.168.0.96`
- **Type-C IP:** `192.168.3.2` (en6, by launchd plist)

## SSH Workflow: `pro` Command (Plain SSH, No tmux)

As of 2026-06-01, the user explicitly rejected tmux. `pro` is now plain SSH:

```zsh
pro() {
    TERM=xterm-256color ssh admin-remote
}
```

No session management, no auto-attach. Just a direct SSH connection. Old `pro_new` and `pro_bash` aliases were removed.

### History: Why tmux Was Removed
- The headless Mac's `~/.tmux.conf` had `set-option -g default-command "reattach-to-user-namespace -l zsh"`
- `reattach-to-user-namespace` was not installed on the headless Mac
- This caused every new tmux session to exit immediately: `[exited]` on connection
- Fix was `sed -i '' '/reattach-to-user-namespace/d' ~/.tmux.conf` + `tmux kill-server`
- User decided they don't need tmux at all → simplified `pro` to plain SSH

**tmux is still installed** on both Macs, just not used in the daily workflow.

## SSH Key Situation

| Key | Passphrase | Purpose |
|-----|-----------|---------|
| `~/.ssh/id_ed25519` | Yes (stored in Keychain) | General use |
| `~/.ssh/id_ed25519_hermes` | Yes | GitHub (China, port 443) |
| `~/.ssh/id_ed25519_headless` | **No** | Display → headless Mac auto-connect |
| `~/.ssh/id_auto_ssh` | TBD | Created for `agy` host, may need setup |

The headless key (`id_ed25519_headless`) was created to bypass the passphrase prompt that blocked Hermes automated SSH. Key was generated with `-N ""` and copied via `sshpass -p '0000' ssh-copy-id`.

## Current Network (Ship WiFi, 2026-06-01)

| | Экранный (dispo) | Безголовый (admin) |
|---|---|---|
| WiFi IP | 192.168.102.14/23 (DHCP) | 192.168.103.70 (static) |
| Интерфейс | en0 | en0 |
| Шлюз | 192.168.102.1 | 192.168.102.1 |

**Recurring problem:** Ship WiFi subnet changes unpredictably (observed: 192.168.102.0/23 → 103.0/23 → 104.0/23 → back to 102.0/23). The headless Mac's static IP (192.168.103.70) may fall outside the current DHCP subnet. See `headless-mac-static-ip` and `ship-wifi-iphone-sharing` skills for workarounds.

**Client isolation:** The ship's WiFi (SJYH) may use client isolation on different APs — from a far deck, the display Mac might not reach the headless Mac even when both are on the same SSID.

## Network Configuration

### Service Order (ZTE Primary — Ship WiFi for local access)
```
1. ZTE USB (en7/en8)     — 192.168.0.96, gw 192.168.0.1 (internet)
2. Wi-Fi (en0)           — 192.168.102.x (ship, local SSH only)
3. Thunderbolt Bridge     — bridge0, 192.168.2.2 (fallback)
```

### Power Management & WiFi Optimization
- **Sleep disabled:** `sudo pmset -a sleep 0 && sudo pmset -a hibernatemode 0`
- **AWDL disabled** (less WiFi contention): `sudo ifconfig awdl0 down`

### Known Issues
See `macos-ssh-setup` SKILL.md pitfalls table for:
- Blurred WiFi toggle fix
- SSH unreachable over WiFi despite ping
- Client isolation on ship APs

## Installed Software

### Tools
- tmux (via brew, exists but unused in daily workflow)
- Python 3.12.8
- Shadowrocket (VPN/proxy)
- Ollama
- LM Studio
