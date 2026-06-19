# Speedify Network Extension — Traffic Interference

## Symptom

- `curl`, `ping`, `nslookup` all work fine on the headless Mac
- Safari (and any NSURLSession-based app) shows "Safari can't establish a secure connection" for ALL sites
- Python `urllib.request.urlopen()` works (same system stack as Safari on some macOS versions) — but Safari doesn't
- `systemextensionsctl list` shows Speedify.PacketTunnelSysExt as `[activated enabled]`

## Root Cause

Speedify installs a **Network Extension** (`com.connectify.Speedify.PacketTunnelSysExt`) that intercepts all system network traffic. When Speedify is disconnected or not logged in, the extension is still active but has no working tunnel → it blocks NSURLSession traffic.

`curl` bypasses this because it uses raw sockets — it does not go through NSURLSession. This is the key diagnostic signal: if raw TCP/TLS work (curl) but higher-level networking doesn't (Safari), suspect a Network Extension.

## Detection

```bash
# List all system extensions
systemextensionsctl list

# Look for:
#   enabled  active  teamID  bundleID                           name
#   *        *       42L9495X72  com.connectify.Speedify.PacketTunnelSysExt  PacketTunnelSysExt  [activated enabled]

# Check Speedify status (if installed)
speedify status
```

## The removal problem

On macOS 14+ with SIP enabled (default on Apple Silicon):

1. `systemextensionsctl uninstall <teamID> <bundleID>` requires SIP off
2. `systemextensionsctl reset` requires SIP off
3. `sudo rm -rf /Library/SystemExtensions/<UUID>/` — SIP blocks write (`Operation not permitted`)
4. `sudo plutil -remove "extensions.0" /Library/SystemExtensions/db.plist` — SIP blocks write

Even deleting the Speedify app and rebooting does NOT deactivate the extension.

## Solutions

### Solution 1: Install Speedify, log in, connect, then properly disconnect
1. Re-install Speedify.app
2. `speedify login` (or create a free account)
3. `speedify connect`
4. `speedify disconnect`
5. `speedify daemon exit`
6. Delete Speedify.app again and reboot

### Solution 2: Configuration Profile (theoretical, requires user to approve in GUI)
Create a `.mobileconfig` with `RemovedSystemExtensions` key for teamID `42L9495X72` and bundleID `com.connectify.Speedify.PacketTunnelSysExt`, then install via System Settings → Privacy & Security → Profiles.

Note: `sudo profiles install` no longer works on macOS 14+.

### Solution 3: Disable SIP (Recovery Mode)
1. Reboot into Recovery Mode (hold power button on Apple Silicon)
2. `csrutil disable`
3. Reboot and run `sudo systemextensionsctl uninstall 42L9495X72 com.connectify.Speedify.PacketTunnelSysExt`
4. Re-enable SIP: reboot to Recovery → `csrutil enable`

### Solution 4: Physical access to target
If you have physical access to the headless Mac:
1. Reboot into Recovery Mode
2. Disable SIP
3. Remove the extension
4. Re-enable SIP

## Prevention

If Speedify is not needed, don't install it — its Network Extension persists even after app deletion.

If Speedify IS needed, ensure it stays connected:
```bash
speedify startupconnect on
```

This way the tunnel is always active when the extension is loaded.
