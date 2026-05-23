---
name: apple-tethering-setup
description: |
  Configure Mac to get internet via iPhone USB tethering. Useful for China network conditions where mobile carrier APN may be more reliable than WiFi for international access. Version 1.0 (iPhone USB network configuration on macOS).
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [apple, iphone, macos, network, tethering]
    category: smart-home
    related_skills: [macos-computer-use, apple-notes]
---

# Apple iPhone USB Tethering Setup on macOS

## Trigger conditions
iPhone connected to Mac via USB cable,需要配置Mac通过iPhone获取互联网连接。适用于中国大陆网络环境作为 WiFi 不稳定时或不可用时的备用方案（使用运营商 APN）。

## Quick status check
```bash
# Verify iPhone USB interface exists
networksetup -listallhardwareports | grep "iPhone USB"

# Check network service order (should show iPhone enabled with *)
networksetup -listnetworkserviceorder

# Verify interface is active
networksetup -getnetworkserviceenabled "iPhone USB"
```

## Setup steps

### 1. Verify iPhone USB interface exists
```bash
networksetup -listallhardwareports | grep "iPhone USB"
# Should show: Device: en7 (may vary)
```

### 2. Check network service order
iPhone USB must be prioritized above Wi-Fi to ensure Mac uses iPhone connection first:

```bash
networksetup -listnetworkserviceorder | head -5
# iPhone USB should appear before Wi-Fi in the list when both enabled
```

### 3. Configure DNS on iPhone USB interface
iPhone may not automatically provide DNS servers, so manually set reliable Chinese-friendly DNS:

```bash
# Set to China Telecom/Telecom Cloud DNS (recommended for China)
networksetup -setdnsservers "iPhone USB" 223.5.5.5 114.114.114.114

# Alternative: Google DNS (may be blocked in China)
networksetup -setdnsservers "iPhone USB" 8.8.8.8 8.8.4.4
```

### 4. Ensure DHCP is enabled on iPhone USB interface
```bash
networksetup -setdhcp "iPhone USB"
# Wait a few seconds for IP assignment to complete
```

### 5. Verify routing via iPhone interface
Check that Mac's default route goes through iPhone USB:

```bash
route -n get default | grep "interface"
# Should show: interface: en7 (or whatever the iPhone USB device is)
```

### 6. Test connectivity to gateway and internet
```bash
# Ping iPhone's USB interface (gateway) - typically 172.20.x.1
route -n get default | grep "gateway" # Get gateway IP
ping -c 3 <gateway-ip>

# Test external connectivity (ICMP may be blocked on cellular)
ping -c 3 <external-ip>
# or test: curl -I https://google.com

# Verify DNS resolves
ping -c 3 google.com || ping6 -c 3 www.google.com
```

## Troubleshooting

### No internet despite correct config
**Most common cause:** iPhone Personal Hotspot not enabled or Cellular Data disabled

1. **Enable on iPhone:** Settings → Cellular (or Mobile Data) → Personal Hotspot
2. Check "Allow Others to Join" is ON  
3. Ensure Cellular Data is enabled for iPhone
4. **Verify SIM has active data plan** — tethering requires mobile internet

### DNS resolution fails but pings work
```bash
# Check what DNS is configured system-wide
networksetup -getdnsservers Wi-Fi

# Manual override in System Settings:
# System Settings → Network → iPhone USB → Configure DNS → Manual → Add servers
```

### Ping fails but browser works (common on cellular)
- Mobile networks often block ICMP ping requests (normal behavior)
- Test with: `curl -I https://google.com` or `wget --spider https://google.com`
- Try different external IPs: 142.250.x.x (Google), 8.8.8.8, etc.

### "No route to host" error persists
```bash
# Check interface state
ifconfig en7 | grep "state"

# Reset and re-apply config
networksetup -setdhcp "iPhone USB"
sleep 5

# Ensure interface is enabled
networksetup -setnetworkserviceenabled "iPhone USB" on

# Reorder if needed (iPhone first)
networksetup -ordernetworkservices "iPhone USB" Wi-Fi "*"
```

### Import: China network environment specifics
```bash
# If using proxy, bypass for iPhone USB traffic  
networksetup -setproxybypassdomains "iPhone USB" "*"

# For direct carrier routing (no WiFi proxy)
networksetup -setv6automatic "iPhone USB"

# Verify no conflicting active connection
networksetup -getinfo en0 | grep "Wi-Fi"  # Wi-Fi should be disabled or lower priority
```

## Reference commands summary
```bash
# Get iPhone interface IP details (DHCP info)
networksetup -getinfo "iPhone USB"

# List all available network services on Mac
networksetup -listallnetworkservices

# Set order: iPhone USB → Wi-Fi (keep existing other services)
networksetup -ordernetworkservices "iPhone USB" Wi-Fi

# Re-enable DHCP on iPhone interface
networksetup -setdhcp "iPhone USB"

# Get current default route details
route -n get default | grep -E "interface|gateway"

# Check interface state and IP
ifconfig en7 | grep -E "inet|state"

# Verify tethering (run the verification script)
./scripts/verify-iphone-tether.sh
```

## Network details from setup
After successful configuration, you should see:
- **Interface:** en7 (iPhone USB)  
- **IP address:** 172.20.x.x (typically .4 as per iPhone's subnet)
- **Subnet mask:** 255.255.255.240
- **Gateway:** 172.20.x.1 (iPhone acting as router)
- **DNS:** 223.5.5.5, 114.114.114.114 (or your chosen DNS)

## Notes for China network environment
- iPhone USB tethering routes traffic through carrier's APN, not WiFi hotspot
- Often more stable for international domains when WiFi is blocked/unreliable  
- Mobile carrier DNS (223.5.5.5, 114.114.x.x) works better than Google DNS in China
- Some apps/ports may have carrier restrictions — expect occasional failures
- Battery drain: iPhone USB tethering consumes mobile data; monitor battery

## Alternative DNS options for China
| Provider | Primary | Secondary | Notes |
|----------|---------|-----------|-------|
| China Telecom Cloud | 223.5.5.5 | 223.6.6.6 | Recommended, fast |
| China Unicom Cloud | 114.114.114.114 | 114.114.115.115 | Widespread use |
| Ali DNS | 240.0.8.x | 240.0.9.x | (1-3) range |
| Google DNS | 8.8.8.8 | 8.8.4.4 | Often blocked in China |

## User preferences integrated
- Direct, efficient communication: Skip verbose explanations when config is working
- China network context: Automatically use Chinese DNS servers; don't suggest Google DNS as default