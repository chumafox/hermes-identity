# Screen Sharing Diagnostic Commands

Quick diagnostic checklist for Screen Sharing between two Macs over Thunderbolt Bridge.

## On both Macs — check bridge status

```bash
# Verify Thunderbolt Bridge is active
ifconfig bridge0 | grep -E 'flags|inet |status'

# Should show: UP,RUNNING,SMART + inet 192.168.2.x + status: active
```

## On headless Mac — check Screen Sharing service

```bash
# Verify VNC is listening on all interfaces
sudo netstat -an -p tcp | grep ':5900'

# Find active VNC session
sudo lsof -iTCP:5900 -P -n | grep ESTABLISHED

# Expected output pattern:
# screensha PID root ... TCP 192.168.2.2:5900->192.168.2.1:49431 (ESTABLISHED)
```

## On headless Mac — verify display

```bash
# Check if headless (no physical monitor)
system_profiler SPDisplaysDataType | grep -A5 "Screen Sharing Virtual Display"

# Check if any physical display is connected
system_profiler SPDisplaysDataType | grep -B1 "Resolution" | grep -v "Screen Sharing"
```

## On headless Mac — check hot corners

```bash
# Check all four corners
defaults read com.apple.dock wvous-tl-corner 2>&1  # top-left
defaults read com.apple.dock wvous-tr-corner 2>&1  # top-right
defaults read com.apple.dock wvous-bl-corner 2>&1  # bottom-left
defaults read com.apple.dock wvous-br-corner 2>&1  # bottom-right
```

## On headless Mac — reset Screen Sharing

```bash
sudo killall screensharingagent
```
