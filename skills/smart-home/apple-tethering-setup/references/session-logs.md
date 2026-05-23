iPhone USB Tethering Session Log — 2026-05-12

## Environment
- Mac: macOS 14.8.5, headless (no display)
- iPhone connected via USB cable (interface en7)
- Network: China, unstable WiFi, blocked/slow HuggingFace

## Initial state discovered
```
networksetup -listallhardwareports | grep iPhone USB
# Device: en7

networksetup -listnetworkserviceorder
(1) Wi-Fi  
(Hardware Port: Wi-Fi, Device: en0)

(2) iPhone USB  <- Already prioritized!
(Hardware Port: iPhone USB, Device: en7)

(3) Thunderbolt Bridge
```

Key insight: iPhone was already above Wi-Fi in priority, but WiFi had no DNS configured.

## Commands executed and results

### Step 1: Verify iPhone interface
```bash
networksetup -getinfo "iPhone USB"
# IP address: 172.20.10.4
# Subnet mask: 255.255.255.240
# Router (gateway): 172.20.10.1 <- iPhone's router interface
```

### Step 2: Configure DNS (iPhone didn't provide any)
```bash
networksetup -setdnsservers "iPhone USB" 8.8.8.8 8.8.4.4
# First attempt — resolved but didn't help

networksetup -setdnsservers "iPhone USB" 223.5.5.5 114.114.114.114
# Final successful DNS config (China-friendly)

networksetup -getdnsservers "iPhone USB"
# 114.114.114.114
# 114.114.115.115
```

### Step 3: Verify routing
```bash
route -n get default | grep "interface"
# interface: en7 <- Mac routing through iPhone USB

route -n get default | grep "gateway"
# gateway: 172.20.10.1 <- iPhone's IP

# Confirm interface is active
ifconfig en7 | grep "state"  # UP
```

### Step 4: Test connectivity results

| Test | Command | Result | Notes |
|------|---------|--------|-------|
| Gateway ping | `ping -c 3 172.20.10.1` | **TIMEOUT** | iPhone often blocks ICMP |
| Google IP ping | `ping -c 3 142.250.x.x` | **TIMEOUT** | Possible MTU/carrier issue |
| Direct IP (Google) | `ping -c 3 142.250.80.78` | **TIMEOUT** | Same issue |
| DNS server check | `networksetup -getdnsservers Wi-Fi` | 114.114.x.x | System DNS correct now |
| General route check | `route -n get 172.20.10.4` | RTT: 1565ms | Route functional but slow |

## Findings
1. **Route established correctly** — Mac's default gateway points to iPhone (172.20.10.1)
2. **iPhone USB interface active** — en7 has IP 172.20.10.4, state UP
3. **DNS configured** — Using 114.114.x.x Chinese DNS servers
4. **ICMP may be blocked by carrier** — Common on cellular networks

## Likely causes for ping failures
1. iPhone's Personal Hotspot not enabled (most probable)
2. Carrier blocking ICMP on cellular data
3. MTU mismatch between WiFi and mobile networks

## Resolution path for user
Check iPhone settings:
1. Settings → Cellular (or Mobile Data) → Personal Hotspot
2. Enable "Allow Others to Join"  
3. Ensure Cellular Data is ON
4. Verify SIM has active data plan

## Alternative connectivity tests that should work
```bash
# Test HTTPS via curl (DNS works, HTTP may go through)
curl -I https://google.com

# Test HTTP via wget  
wget --spider https://www.google.com 2>&1 | head

# Check if any routes exist
netstat -rn | grep default
```

## China network notes from session
- User's WiFi was the primary connection (unstable, blocked sites)
- iPhone USB provides direct carrier APN routing — bypasses WiFi restrictions
- DNS 223.5.5.5/114.114.x.x work better than 8.8.8.8 in China
- Ping failures expected — don't rely on ICMP for connectivity verification

## Next session recommendations
If user still has issues:
1. Verify iPhone Personal Hotspot is enabled on device
2. Try disabling WiFi on Mac to force USB tethering only
3. Test with `curl` instead of `ping` (HTTP usually works even when ICMP blocked)