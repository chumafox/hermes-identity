# Headless Mac Admin Connection

**Updated: 2026-05-23**

## Machine
- Model: MacBook Pro 16" 2021 (MacBookPro18,1)
- Chip: Apple M1 Pro (10-core: 8p + 2e)
- RAM: 32 GB
- macOS: 15.7.5 (Sequoia)

## Connection Details
- **Username:** `admin`
- **Password:** `0000`
- **SSH method:** `sshpass -p '0000' ssh -o StrictHostKeyChecking=no admin@IP`
- **Thunderbolt Bridge IP:** `192.168.2.2` (bridge0, ~0.7ms latency) — most reliable
- **WiFi IP:** `192.168.0.174` (ZTE_27AA28, mobile router with SIM, WiFi 7 capable)
- **Type-C IP:** `192.168.3.2` (en6, by launchd plist)

## Network Configuration

### Service Order (WiFi Primary — ZTE as main route)
```
1. Wi-Fi (en0)           — 192.168.0.174, gw 192.168.0.1 (ZTE, large data plan, primary default route)
2. Thunderbolt Bridge     — bridge0, 192.168.2.2 (fallback)
3. iPhone USB             — en7
4. Shadowrocket
```

Set with: `sudo networksetup -ordernetworkservices "Wi-Fi" "Thunderbolt Bridge" "iPhone USB" "Shadowrocket"`

### Power Management & WiFi Optimization
- **Sleep disabled:** `sudo pmset -a sleep 0 && sudo pmset -a hibernatemode 0`
- **AWDL disabled** (less WiFi contention): `sudo ifconfig awdl0 down`
- **Preferred network:** ZTE_27AA28 (WPA2, 5 GHz, 80 MHz, 1200 Mbps PHY rate)
- **Signal:** -34 to -39 dBm (excellent), Noise: -90 dBm

### WiFi Throughput (real, via SCP 50MB test)
- **WiFi (ZTE router):** ~128 Mbps (16 MB/s) — bottleneck: router CPU switching between WiFi clients
- **Thunderbolt Bridge:** ~595 Mbps (74 MB/s) — bottleneck: SCP/SSH encryption overhead on M1 Pro
- **Raw TCP (theoretical):** ~200 Mbps WiFi, ~900 Mbps TB

### Known Issue: Blurred WiFi Toggle
When WiFi toggle is greyed out in System Settings → Network:
1. Diagnose: `networksetup -listnetworkserviceorder | grep -E "Wi-Fi|\\*"` — look for `(*) Wi-Fi`
2. Fix: `sudo networksetup -setnetworkserviceenabled "Wi-Fi" on`
3. Turn WiFi power on: `sudo networksetup -setairportpower en0 on`
4. Verify: `sudo wdutil info 2>&1 | grep -E "Power|Op Mode|SSID"` should show STA + SSID

### Known Issue: SSH Unreachable Over WiFi
Host pings on 192.168.0.174 (ICMP works) but port 22 times out.
**Most common cause:** Mac went to sleep (sshd stops). Fix: disable sleep (see above).
**Second cause:** sshd bound only to a specific interface. Fix via TB SSH:
```bash
sudo launchctl kickstart -k system/com.openssh.sshd
sudo lsof -i :22 -P -n 2>/dev/null | grep LISTEN  # verify *:22
```

## Installed Software

### ML/AI
- Python 3.12.8 (from screen Mac bundled copy)
- MLX stack: none installed yet
- OpenVox: not installed on this Mac

### Networking Tools
- Shadowrocket (VPN/proxy)
- ZTE_27AA28 mobile router (WiFi 7 capable, SIM card with large data plan)
- Thunderbolt Bridge (10 Gbps link)
- Type-C: 192.168.3.2 (static)
- iPhone USB: 172.20.10.x (via en7, when plugged)

## Notes
- `brew` not available — use full path `/opt/homebrew/bin/brew` or install via transfer
- Default route via WiFi (192.168.0.1, ZTE router)
- Thunderbolt Bridge is fallback for internet but works as management channel
- Both Macs on same subnet 192.168.0.0/24 — direct communication (via WiFi router) works
- Screen Mac: 192.168.0.82 (en0, same ZTE WiFi network)
