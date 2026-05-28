# USB-C Static IP Setup

When two Macs are connected directly via USB-C (not Thunderbolt), they get a **Link-Local** IP (169.254.x.x) that changes every reconnect. To get a stable address, assign static IPs.

## Prerequisites

- Both Macs connected via USB-C cable
- Identify which interface handles USB-C on each Mac:
  ```bash
  # On both Macs, look for interfaces with 169.254.x.x addresses
  ifconfig | grep -B1 "inet 169.254"
  ```

## Setup: Headless Mac (target)

Create a network service for the USB-C interface and assign a static IP:

```bash
# 1. Find the interface name (e.g., en6, en8)
# Look for the one with 169.254.x.x that's NOT Thunderbolt bridge

# 2. Create service (one-time)
sudo networksetup -createnetworkservice "USB-C Ethernet" en6

# 3. Assign static IP
sudo networksetup -setmanual "USB-C Ethernet" 192.168.3.2 255.255.255.0 192.168.3.1
#                                     ^-- IP on headless     ^-- mask    ^-- gateway (screen Mac)

# 4. Restart interface to apply
sudo ifconfig en6 down && sleep 1 && sudo ifconfig en6 up

# 5. Verify
ifconfig en6 | grep "inet "  # → 192.168.3.2
```

## Setup: Screen Mac

On the screen Mac, the USB-C interface may NOT be registered as a `networksetup` hardware port. If `sudo networksetup -createnetworkservice "USB-C Link" en7` fails with `en7 is not a valid hardware port name`, use a LaunchDaemon instead:

```bash
# Create launchd plist that assigns IP at boot
sudo tee /Library/LaunchDaemons/com.local.usb-c-ip.plist > /dev/null << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.usb-c-ip</string>
    <key>ProgramArguments</key>
    <array>
        <string>/sbin/ifconfig</string>
        <string>en7</string>
        <string>inet</string>
        <string>192.168.3.1</string>
        <string>netmask</string>
        <string>255.255.255.0</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

# Load
sudo launchctl load -w /Library/LaunchDaemons/com.local.usb-c-ip.plist

# Verify
sudo launchctl list | grep usb-c  # → -    0    com.local.usb-c-ip
ifconfig en7 | grep "inet "       # → 192.168.3.1
```

## Usage

After setup, connect via static IP:

```bash
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.3.2
```

This IP **does not change** on cable reconnect, unlike 169.254.x.x link-local addresses.

## Pitfalls

- **Interface name changes** — `en7` on one Mac may be `en6` on another. Check with `ifconfig` after connecting the cable.
- **Same subnet** — Use 192.168.3.x (does not conflict with Thunderbolt Bridge 192.168.2.x or iPhone USB 172.20.10.x).
- **Thunderbolt Bridge still preferred** — Static USB-C is a fallback when Thunderbolt cable isn't connected. Keep Thunderbolt as primary for speed.
- **Both IPs active simultaneously** — If both USB-C and Thunderbolt are connected, macOS routes traffic to the most specific route. Both work.
