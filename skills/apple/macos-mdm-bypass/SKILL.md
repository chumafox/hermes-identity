---
name: macos-mdm-bypass
category: apple
description: Detect, block, and bypass MDM/DEP enrollment on macOS. Covers second-hand Macs with organizational DEP locks (Jamf, Mosyle, Kandji, etc.), forced enrollment windows, and permanent prevention.
tags: [macos, mdm, dep, enrollment, jamf, mac-second-hand, bypass, enterprise]
triggers:
  - user finds an MDM/DEP enrollment window on a Mac, "Enroll" is the only option
  - user bought a second-hand Mac that was previously enterprise-managed
  - user asks to remove/block MDM enrollment
  - user reports a Setup Assistant window with "walmart.jamfcloud.com" or similar MDM URL
  - user wants to prevent MDM enrollment on a headless/SSH-accessible Mac
---

# macOS MDM/DEP Bypass

Bypass Mobile Device Management (MDM) / Device Enrollment Program (DEP) enrollment on macOS. Works on Macs where you have SSH or physical access with an existing admin user.

## Detection

SSH into the target Mac and check enrollment status:

```bash
# Check if enrolled
profiles status -type enrollment

# Show DEP configuration (URL, organization, skip setup list)
sudo profiles show -type enrollment

# Look for running MDM processes
ps aux | grep -i "mdmclient\|Setup Assistant.*ForceMDMEnroll"
```

Key indicators in `profiles show -type enrollment`:
- `IsMandatory = 1` — enrollment forced, no skip option in UI
- `IsSupervised = 1` — Mac is supervision-mode capable
- `ConfigurationURL` — the MDM server (e.g. `https://walmart.jamfcloud.com/cloudenroll`)
- `OrganizationName` — the org that locked the device (e.g. "Wal-mart.com Usa, Llc")

## Bypass Procedure (with admin SSH access)

### Step 1: Kill running enrollment processes

```bash
sudo pkill -9 -f "Setup Assistant"
sudo pkill -9 -f mdmclient
```

The Setup Assistant process with `-ForceMDMEnroll` flag controls the enrollment window. Killing it removes the dialog from screen immediately.

### Step 2: DNS-block all MDM and DEP servers in /etc/hosts

Block both the specific MDM server AND Apple's DEP infrastructure:

```bash
# Apple DEP/MDM infrastructure
echo "0.0.0.0 deviceenrollment.apple.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 gdmf.apple.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 deviceservices.apple.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 mdmenrollment.apple.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 iprofiles.apple.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 iprofiles.mac.com" | sudo tee -a /etc/hosts

# Your specific MDM server (check URL from `sudo profiles show -type enrollment`)
echo "0.0.0.0 walmart.jamfcloud.com" | sudo tee -a /etc/hosts
```

Without these blocks, the Mac contacts Apple's DEP servers on every boot, gets the MDM URL, and re-triggers enrollment.

### Step 3: Create Setup Assistant done marker

```bash
sudo touch /var/db/.AppleSetupDone
```

This tells macOS that initial setup is complete. Setup Assistant will not launch on subsequent boots.

### Step 4: Disable mdmclient launchd service

```bash
sudo launchctl disable system/com.apple.mdmclient.daemon
sudo launchctl disable gui/501/com.apple.mdmclient.agent
```

This prevents mdmclient from auto-restarting when killed.

### Step 5: Flush DNS cache

```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### Step 6: Deploy watchdog launchd agent (immediate relief)

If the enrollment window keeps reappearing even after killing processes (mdmclient is a
launchd-supervised service and respawns), deploy a launchd agent that kills it every
30 seconds. This gives immediate relief without rebooting.

Copy the template from `templates/com.user.kill-mdm.plist` to the remote Mac,
or inline it:

```bash
# Create the plist on the remote Mac
cat > ~/Library/LaunchAgents/com.user.kill-mdm.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.kill-mdm</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>pkill -9 -f "mdmclient"; pkill -9 -f "Setup Assistant"</string>
    </array>
    <key>StartInterval</key>
    <integer>30</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/dev/null</string>
    <key>StandardErrorPath</key>
    <string>/dev/null</string>
</dict>
</plist>
PLIST

# Load it (starts immediately, then every 30s)
launchctl load ~/Library/LaunchAgents/com.user.kill-mdm.plist

# Verify
launchctl list com.user.kill-mdm
```

The agent starts at load (`RunAtLoad = true`) and fires every 30 seconds (`StartInterval = 30`).
It sends all output to /dev/null so it doesn't fill logs.

**Adjusting frequency:** If the enrollment window still briefly appears before being killed,
change `StartInterval` to `5` (every 5 seconds). This is aggressive but uses negligible CPU
(the pkill exits in <1ms). Load with launchctl after changing. Recommended when the user
reports the window visibly reappearing at 30s intervals.

You can also copy `scripts/kill-mdm.sh` to `/usr/local/bin/` on the remote Mac for
standalone use, or reference it from the launchd agent's ProgramArguments instead of
the inline pkill command.

## Permanent Fix: Remove Cloud Config (requires physical access + SIP disable)

For a truly permanent fix that survives OS updates and NVRAM resets, remove the SIP-protected cloud config files by booting into Recovery Mode.

### Step 1: Boot into Recovery

**Apple Silicon (M1/M2/M3/M4):**
1. Shut down completely (hold power for 10s if needed)
2. Press and HOLD the power button until "Loading startup options..." appears
3. Click Options -> Continue
4. Select admin user, enter password

**Intel Mac:**
1. Restart with Cmd+R held until Recovery loads

### Step 2: Disable SIP

In Recovery: Utilities -> Terminal, then:

```bash
# Full disable
csrutil disable

# OR safer: disable only filesystem protection
csrutil enable --without fs
```

Quit Terminal, restart (Apple menu -> Restart).

### Step 3: Remove Cloud Config Files

After reboot, the Mac loads macOS with SIP disabled. SSH or local terminal:

```bash
cd /var/db/ConfigurationProfiles/Settings/
sudo rm -f .cloudConfigHasActivationRecord
sudo rm -f .cloudConfigRecordFound
sudo rm -f .cloudConfigTimerCheck
sudo rm -f .profilesDEPTimerCheck

# Verify
ls -la /var/db/ConfigurationProfiles/Settings/ | grep cloud
# → empty
```

### Step 4: Re-enable SIP

Boot into Recovery again (Step 1), then:

```bash
csrutil enable
```

Restart.

### Step 5: Verify

```bash
profiles status -type enrollment
# Enrolled via DEP: No
# MDM enrollment: No
```

### Why This Works

The files `.cloudConfigHasActivationRecord`, `.cloudConfigRecordFound` etc. are created during the initial DEP check and stored in the SIP-protected `/var/db/ConfigurationProfiles/Settings/` directory. Even as root, they cannot be modified. These files tell macOS: "this device has a DEP enrollment record — show Setup Assistant with ForceMDMEnroll." Removing them stops the enrollment trigger at the source.

## Verification

```bash
# Check no MDM/Setup processes remain
ps aux | grep -i "mdmclient\|Setup Assistant" | grep -v grep
# → empty

# Verify DNS blocks
dscacheutil -q host -a name walmart.jamfcloud.com
# → ip_address: 0.0.0.0

# Verify Setup Assistant won't launch
ls -la /var/db/.AppleSetupDone
# → -r--------  1 root  wheel  0 ...
```

## Pitfalls

### SIP (System Integrity Protection) blocks file deletion

Files in `/var/db/ConfigurationProfiles/Settings/` (where cloud config records live) are SIP-protected. Even `root` cannot delete them:

```bash
sudo rm -rf /var/db/ConfigurationProfiles/Settings/.cloudConfig*
# → Operation not permitted
```

**Workaround:** Do NOT rely on deleting these files. The DNS + launchd disable + .AppleSetupDone + watchdog approach works without touching SIP. Booting into Recovery Mode to disable SIP is not feasible on headless/remote Macs.

### crontab blocked by SIP / Full Disk Access

On modern macOS (Ventura+), `crontab` may fail with `Operation not permitted` even as root:

```bash
crontab -l  # crontab: tmp/tmp.xxx: Operation not permitted
```

**Workaround:** Use a user-level launchd agent instead. See Step 6 (watchdog approach) — it's
the SIP-safe equivalent of a cron job. User LaunchAgents in `~/Library/LaunchAgents/` are
not subject to the same SIP restrictions as system crontab.

### mdmclient may still run after kill

Even after `pkill -9`, mdmclient is a launchd-managed service. It may be respawned.
Combining launchctl disable + DNS block prevents it from doing any harm.

**Check both launchd variants:** `sudo launchctl print-disabled system | grep mdm` lists disabled services.
If only `mdmclient.daemon.runatboot` shows as disabled but `mdmclient.daemon` is not, enable the latter too:

```bash
sudo launchctl disable system/com.apple.mdmclient.daemon
sudo launchctl disable system/com.apple.mdmclient.daemon.runatboot
```

### Reboot will re-enable the enrollment dialog IF .AppleSetupDone isn't present

Always create `.AppleSetupDone` before rebooting. Without it, Setup Assistant re-launches and shows the enrollment window again.

### DNS blocks erase on system update

macOS updates may use their own DNS resolver that bypasses /etc/hosts. After a major OS update, verify the host entries are still present.

### /etc/hosts deduplication from repeated tee -a

Using `tee -a` for each host entry adds duplicate lines if the command is
re-run. Clean duplicates with:

```bash
sudo sed -i "" '/^0\.0\.0\.0.*jamfcloud/d' /etc/hosts
sudo sed -i "" '/^0\.0\.0\.0.*deviceenrollment/d' /etc/hosts
sudo sed -i "" '/^0\.0\.0\.0.*gdmf/d' /etc/hosts
sudo sed -i "" '/^0\.0\.0\.0.*deviceservices/d' /etc/hosts
```

Then re-add the entries cleanly. Or use a single `printf` + `tee` instead
of repeated `tee -a`.

### macOS Sequoia TCC blocks SSH access to user data

On macOS 15 (Sequoia), SSH sessions cannot access `~/Documents/` even with sudo. Commands like `cp`, `ls`, `scp` all fail with `Operation not permitted` when targeting ~/Documents. This affects the watchdog script if it's stored in ~/Documents — keep it in ~/ or /tmp/ instead.

**Workaround for copying files FROM a Sequoia Mac:** Use `open -a Terminal` to launch a script in the GUI Terminal.app context (which has Full Disk Access). See china-networking skill for the full reverse SSH push procedure.

### Setup Assistant can re-appear

If the Mac serial number is still in Apple Business Manager / DEP, the enrollment can re-trigger on certain events (OS updates, NVRAM reset, SMC reset). The DNS blocks are your primary defense.

## References

See `references/jamfcloud-dep-example.md` for a real-world Walmart/Jamf Cloud DEP configuration from a second-hand Mac.

### Linked files in this skill

| File | Purpose |
|------|---------|
| `references/jamfcloud-dep-example.md` | Real-world Jamf Cloud DEP config dump |
| `scripts/kill-mdm.sh` | Standalone script to kill mdmclient + Setup Assistant |
| `templates/com.user.kill-mdm.plist` | Launchd agent template for watchdog (every 30s) |
