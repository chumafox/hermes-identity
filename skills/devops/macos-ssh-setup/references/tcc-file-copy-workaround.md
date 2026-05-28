# TCC/Full Disk Access File Copy Workaround (macOS 15+)

## Problem
SSH sessions cannot access ~/Documents on macOS 15+ even as root. TCC denies it.

## Solution
Run the copy through the user's Terminal.app (has FDA by default).

## When to Use
- Need to copy files from a headless Mac's ~/Documents to another machine
- Standard SSH/SCP fails with "Operation not permitted"
- No physical access to disable SIP
- Screen is reachable via Screen Sharing (VNC)

## Step-by-Step

### 1. Write a copy script on the remote
```bash
cat > /tmp/copy.sh << 'SCRIPT'
#!/bin/bash
cp -R /Users/admin/Documents/SourceDir /tmp/dest
chmod -R 755 /tmp/dest
SCRIPT
chmod +x /tmp/copy.sh
```

### 2. Launch via Terminal.app (GUI context)
```bash
ssh admin@remote 'open -a Terminal /tmp/copy.sh'
```

This opens a Terminal window on the remote Mac's desktop and runs the script. Terminal.app has Full Disk Access → can read ~/Documents.

### 3. Verify and copy
```bash
sleep 5
ssh admin@remote 'ls /tmp/dest'
scp -r admin@remote:/tmp/dest /local/path/
```

## Limitations
- **Screen must be unlocked** — if the remote Mac's screen is locked (showing login window), `open -a Terminal` will start the app but it won't have a valid GUI session context and the script may not get TCC access.
  - To unlock remotely: connect via Screen Sharing (VNC), the lock screen appears. Click to get the password field, type the user's password, press Enter. Then the GUI context is active.
  - Alternative: Use SSH to check `ps aux | grep loginwindow` — if only one loginwindow process is running and it's the `console` user, the session is active (but may still be locked at screen level).
- Script runs as the logged-in GUI user, not root.
- Terminal.app must be available (always is on macOS).
- Files copied to /tmp are accessible from SSH normally.

## Alternative: Reverse SSH (Headless Pushes to Display)

When the remote Mac's screen is **locked** (so `open -a Terminal` hangs), use the **reverse approach**: the headless Mac SSHs into the display Mac and pushes files.

### Setup

Generate a temporary SSH key on the display Mac, add to authorized_keys, copy the private key to headless, then have headless scp/rsync files to display. This works because the display Mac's SSH is the receiver and doesn't need TCC access.

**Pitfall:** This only works if the headless Mac CAN read the source files locally. If TCC blocks SSH on the headless too (files are in ~/Documents), you must unlock the screen and use the Terminal.app workaround above.

## macOS 15+ crontab Blocked

`crontab` on macOS 15+ may fail with `Operation not permitted` due to SIP. Use `launchctl` agents instead (see `references/mdm-dep-bypass.md` for a watchdog plist template).

## Why Not Sudo?
On macOS 15+, TCC enforcement overrides root for protected paths even with `sudo`. The only alternatives without GUI context are:
1. Boot Recovery → `csrutil disable` → remove files → re-enable SIP
2. Use a process that already has FDA (Terminal, Finder, some background services)
3. Open the TCC.db (also SIP-protected on Sequoia)
